import json
import os
from shared.config import USER_DB_PATH, SHIFTS_DB_PATH, EMPLOYEES_DB_PATH
from shared.logger import logger

def load_user_db():
    """Загружает базу данных пользователей"""
    if not os.path.exists(USER_DB_PATH):
        return {}
    try:
        with open(USER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_user_db(data):
    """Сохраняет базу данных пользователей"""
    try:
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        with open(USER_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении базы пользователей: {e}")
        return False

def get_user_employee(telegram_id):
    """Получает сотрудника, связанного с Telegram ID"""
    users = load_user_db()
    return users.get(str(telegram_id))

def save_user_employee(telegram_id, employee_name):
    """Сохраняет связь между Telegram ID и сотрудником"""
    users = load_user_db()
    users[str(telegram_id)] = employee_name
    return save_user_db(users)

def remove_user_employee(telegram_id):
    """Удаляет связь между Telegram ID и сотрудником"""
    users = load_user_db()
    if str(telegram_id) in users:
        del users[str(telegram_id)]
        return save_user_db(users)
    return True

def load_shifts():
    if not os.path.exists(SHIFTS_DB_PATH):
        logger.warning(f"Файл {SHIFTS_DB_PATH} не найден, создаю пустой")
        with open(SHIFTS_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []
    try:
        with open(SHIFTS_DB_PATH, 'r', encoding='utf-8') as f:
            shifts = json.load(f)
            logger.info(f"Загружено {len(shifts)} смен из shifts.json")
            return shifts
    except json.JSONDecodeError:
        logger.error(f"Ошибка при чтении {SHIFTS_DB_PATH}. Файл поврежден.")
        return []

def load_employees():
    """Загружает список сотрудников из БД"""
    try:
        with open(EMPLOYEES_DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('employees', [])
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка сотрудников: {e}")
        return []

def save_employees(employees_list):
    """Сохраняет список сотрудников в БД"""
    try:
        with open(EMPLOYEES_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({'employees': employees_list}, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении списка сотрудников: {e}")
        return False
