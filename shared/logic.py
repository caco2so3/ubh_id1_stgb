from shared.sheet_parser import get_shifts_from_sheet
from shared.user_db import save_shifts_to_db, get_user_shift
from shared.logger import logger

def refresh_and_get_shifts():
    try:
        shifts = get_shifts_from_sheet()
        save_shifts_to_db(shifts)
        logger.info("Смены обновлены и сохранены.")
        return shifts
    except Exception as e:
        logger.error(f"Ошибка при обновлении смен: {e}")
        raise

def get_shift_for_user(username):
    try:
        shift = get_user_shift(username)
        logger.debug(f"Смена для пользователя {username}: {shift}")
        return shift
    except Exception as e:
        logger.error(f"Ошибка при получении смены пользователя {username}: {e}")
        return None
