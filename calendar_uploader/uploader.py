from shared.logger import logger
from shared.calendar_api import (
    get_calendar_service, 
    load_shifts_from_db, 
    upsert_shift_event,
    save_shifts
)
from shared.sheet_parser import sync_shifts_to_json
from shared.config import SHIFTS_DB_PATH
from datetime import datetime, timedelta
import asyncio

def get_current_week():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday

def has_next_week_shifts():
    """Проверяет, есть ли смены на следующую неделю"""
    logger.debug("Проверка наличия смен на следующую неделю")
    shifts = load_shifts_from_db()
    if not shifts:
        logger.info("Нет сохраненных смен")
        return False
        
    current_week = get_current_week()
    next_week = current_week + timedelta(weeks=1)
    next_week_end = next_week + timedelta(days=6)
    
    for shift in shifts:
        try:
            shift_date = datetime.strptime(shift['start_time'], '%Y-%m-%d %H:%M:%S')
            if next_week.date() <= shift_date.date() <= next_week_end.date():
                logger.debug(f"Найдена смена на следующую неделю: {shift['employee_name']} на {shift_date}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при проверке смены: {e}")
            continue
            
    logger.info("Смен на следующую неделю не найдено")
    return False

def upload_shifts(force: bool = False):
    """Загружает смены из JSON в Google Calendar
    
    Args:
        force (bool): Если True, загружает все смены без проверки даты (ручной режим)
    """
    logger.info(f"Запуск загрузки смен (force={force})")
    
    logger.debug("Запуск синхронизации с Google таблицей")
    if sync_shifts_to_json(force=force):
        logger.info("Синхронизация с таблицей успешна")
    else:
        logger.warning("Синхронизация с таблицей не удалась")
        return
    
    if not force:
        if not has_next_week_shifts():
            logger.info("Нет смен на следующую неделю, пропускаем автоматическую загрузку")
            return
        logger.info("Найдены смены на следующую неделю, продолжаем автоматическую загрузку")
        
    shifts = load_shifts_from_db()
    if not shifts:
        logger.warning("Нет смен для загрузки в календарь")
        return

    try:
        service = get_calendar_service()
        logger.debug("Сервис календаря получен успешно")
        
        for shift in shifts:
            try:
                upsert_shift_event(service, shift, force=force)
            except Exception as e:
                logger.error(f"Ошибка при обработке смены {shift.get('employee_name')}: {e}")
        
        logger.info("Загрузка смен в календарь завершена")
    except Exception as e:
        logger.error(f"Критическая ошибка при загрузке смен: {e}")
        raise

async def run_uploader():
    """Запускает автоматическую загрузку смен"""
    logger.info("Запуск загрузчика смен в календарь...")
    while True:
        try:
            upload_shifts()  # Автоматическая загрузка только для следующей недели
            logger.info("Загрузка смен успешно завершена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке смен: {e}")
        
        await asyncio.sleep(300)
        logger.debug("Следующая проверка смен...")
