import schedule
import time
import asyncio
from datetime import datetime
from shared.logger import logger
from shared.sheet_parser import sync_shifts_to_json
from calendar_uploader.uploader import upload_shifts

def sync_and_upload():
    """Синхронизация данных из таблицы и загрузка в календарь"""
    logger.info("Запуск регулярной синхронизации смен на следующую неделю...")
    try:
        logger.debug("Запуск синхронизации с Google таблицей")
        if sync_shifts_to_json():
            logger.info("Синхронизация с таблицей успешна, начинаю загрузку в календарь")
            upload_shifts()  # Загружаем только смены на следующую неделю
            logger.info("Регулярная синхронизация успешно завершена")
        else:
            logger.error("Синхронизация смен с таблицей не удалась")
    except Exception as e:
        logger.error(f"Критическая ошибка при регулярной синхронизации: {e}")

def run_scheduler():
    """Запуск планировщика задач"""
    logger.info("Инициализация планировщика задач")
    schedule.every().friday.at("18:00").do(sync_and_upload)
    logger.info("Установлено расписание: каждая пятница в 18:00")
    
    now = datetime.now()
    if now.weekday() == 4 and now.hour >= 18:  # Пятница после 18:00
        logger.info("Обнаружен первый запуск в пятницу после 18:00, выполняю синхронизацию")
        sync_and_upload()
    
    logger.info("Планировщик запущен и готов к работе")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Ошибка в цикле планировщика: {e}")
            time.sleep(60)  # Продолжаем работу даже при ошибке

async def run_uploader():
    """Асинхронная функция для запуска загрузчика смен"""
    logger.info("Инициализация загрузчика смен...")
    while True:
        try:
            upload_shifts()  # Загружает только смены на следующую неделю
            logger.debug("Проверка смен завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка при проверке смен: {e}")
        
        await asyncio.sleep(300)  # Проверяем каждые 5 минут
        logger.debug("Следующая проверка смен через 5 минут")
