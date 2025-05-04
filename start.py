import os
import json
import asyncio
from shared.config import (
    TELEGRAM_TOKEN, DATABASE_DIR, DATA_DIR, LOGS_DIR,
    USER_DB_PATH, SHIFTS_DB_PATH, EMPLOYEES_DB_PATH, LOG_FILE_PATH
)
from shared.logger import logger
from tg_bot.bot import run_bot
from calendar_uploader.uploader import run_uploader

if not TELEGRAM_TOKEN:
    logger.critical("TELEGRAM_TOKEN не найден в .env файле")
    raise ValueError("TELEGRAM_TOKEN не найден в .env файле")

def init_project_structure():
    """Инициализирует структуру проекта и необходимые файлы"""
    for directory in [DATABASE_DIR, DATA_DIR, LOGS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Создана директория: {directory}")

    json_files = {
        USER_DB_PATH: {},
        SHIFTS_DB_PATH: [],
        EMPLOYEES_DB_PATH: {"employees": []}
    }

    for file_path, default_content in json_files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            logger.info(f"Создан файл: {file_path}")

async def main():
    """Главная функция приложения"""
    logger.info("Запуск системы Barhub...")
    logger.debug("Инициализация главного цикла...")
    
    init_project_structure()
    
    logger.info("Barhub стартует 🚀")
    logger.debug("Запуск бота и календарного аплоудера...")
    
    await asyncio.gather(
        run_bot(),
        run_uploader()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error("Критическая ошибка при запуске:", exc_info=True)
        raise
