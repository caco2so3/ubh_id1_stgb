import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from shared.config import TELEGRAM_TOKEN
from shared.logger import logger

load_dotenv()

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

async def setup_handlers():
    from tg_bot.handlers.main_menu import register_handlers
    register_handlers(dp)
    logger.info("Обработчики бота зарегистрированы")

async def run_bot():
    try:
        logger.info("Запуск Telegram-бота...")
        await setup_handlers()
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(run_bot())  # Запуск с asyncio
    except Exception as e:
        logger.exception("Ошибка при запуске бота")
