import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, 'data', '.env'))

DATABASE_DIR = os.path.join(BASE_DIR, os.getenv('DATABASE_DIR', 'database'))
DATA_DIR = os.path.join(BASE_DIR, os.getenv('DATA_DIR', 'data'))
LOGS_DIR = os.path.join(BASE_DIR, os.getenv('LOGS_DIR', 'logs'))

GOOGLE_CREDS_PATH = os.path.join(DATA_DIR, 'creds.json')
USER_DB_PATH = os.path.join(DATA_DIR, 'users.json')
SHIFTS_DB_PATH = os.path.join(DATABASE_DIR, 'shifts.json')
EMPLOYEES_DB_PATH = os.path.join(DATABASE_DIR, 'employees.json')
LOG_FILE_PATH = os.path.join(LOGS_DIR, 'barhub.log')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CALENDAR_ID = os.getenv('CALENDAR_ID')

SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1d8dCGCC7Gx0MQnPAWVr9ny9jOg9Tq5yQOro8yh3aZms/edit?usp=sharing'
SPREADSHEET_ID = '1d8dCGCC7Gx0MQnPAWVr9ny9jOg9Tq5yQOro8yh3aZms'  # оставляем для обратной совместимости

TIMEZONE = os.getenv('TIMEZONE', 'Asia/Yekaterinburg')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

required_vars = [
    ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
    ('CALENDAR_ID', CALENDAR_ID),
    ('SPREADSHEET_ID', SPREADSHEET_ID),
]

for var_name, var_value in required_vars:
    if not var_value:
        raise ValueError(f"Обязательная переменная окружения {var_name} не установлена")
