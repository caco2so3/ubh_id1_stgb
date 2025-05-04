import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from shared.config import (
    GOOGLE_CREDS_PATH, 
    CALENDAR_ID, 
    SHIFTS_DB_PATH,
    TIMEZONE
)

logger = logging.getLogger('barhub')
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Создает и возвращает сервис Google Calendar API"""
    logger.debug(f"Попытка создания сервиса календаря с файлом {GOOGLE_CREDS_PATH}")
    
    if not os.path.exists(GOOGLE_CREDS_PATH):
        logger.error(f"Не найден файл авторизации: {GOOGLE_CREDS_PATH}")
        raise FileNotFoundError("Google credentials file not found")

    try:
        logger.debug("Загрузка учетных данных из файла...")
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar API авторизован успешно")
        return service
    except Exception as e:
        logger.error(f"Ошибка при создании сервиса календаря: {str(e)}")
        raise

def save_shifts(shifts: list, path: str = SHIFTS_DB_PATH) -> None:
    """Сохраняет список смен в JSON-файл"""
    logger.debug(f"Попытка сохранения {len(shifts)} смен в {path}")
    
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Создана директория для хранения смен: {dir_path}")
        except Exception as e:
            logger.error(f"Не удалось создать директорию {dir_path}: {e}")
            raise

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(shifts, f, ensure_ascii=False, indent=4)
        logger.info(f"Успешно сохранено {len(shifts)} смен в {path}")
    except Exception as e:
        logger.exception(f"Ошибка при сохранении смен в {path}: {e}")
        raise

def load_shifts_from_db() -> list:
    """Загружает смены из JSON файла"""
    logger.debug(f"Попытка загрузки смен из {SHIFTS_DB_PATH}")
    
    if not os.path.exists(SHIFTS_DB_PATH):
        logger.warning(f"Файл {SHIFTS_DB_PATH} не найден")
        return []
        
    try:
        with open(SHIFTS_DB_PATH, 'r', encoding='utf-8') as f:
            shifts = json.load(f)
        logger.info(f"Успешно загружено {len(shifts)} смен из {SHIFTS_DB_PATH}")
        return shifts
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении {SHIFTS_DB_PATH}. Файл поврежден: {e}")
        return []
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при загрузке смен: {e}")
        return []

def format_datetime_for_google(dt: datetime) -> str:
    """Форматирует datetime для Google Calendar с учетом таймзоны"""
    logger.debug(f"Форматирование даты {dt} с таймзоной {TIMEZONE}")
    if TIMEZONE == 'Asia/Yekaterinburg':
        return dt.strftime("%Y-%m-%dT%H:%M:%S+05:00")
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

def is_next_week_shift(shift_date: datetime) -> bool:
    """Проверяет, относится ли смена к следующей неделе"""
    today = datetime.now()
    current_week_start = today - timedelta(days=today.weekday())
    next_week_start = current_week_start + timedelta(weeks=1)
    next_week_end = next_week_start + timedelta(days=6)
    
    is_next = next_week_start.date() <= shift_date.date() <= next_week_end.date()
    logger.debug(f"Проверка смены на {shift_date.date()}: следующая неделя - {is_next}")
    return is_next

def find_existing_event(service, summary: str, start_dt: datetime):
    """Ищет существующее событие в календаре"""
    logger.debug(f"Поиск события '{summary}' на {start_dt}")
    try:
        start = format_datetime_for_google(start_dt.replace(hour=0, minute=0, second=0))
        end = format_datetime_for_google(start_dt.replace(hour=23, minute=59, second=59))
        
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start,
            timeMax=end,
            q=summary,
            singleEvents=True,
            timeZone=TIMEZONE
        ).execute()
        
        events = events_result.get('items', [])
        found_event = next((ev for ev in events if ev.get('summary') == summary), None)
        
        if found_event:
            logger.debug(f"Найдено существующее событие: {found_event.get('id')}")
        else:
            logger.debug("Существующее событие не найдено")
            
        return found_event
    except Exception as e:
        logger.error(f"Ошибка при поиске события: {e}")
        return None

def upsert_shift_event(service, shift: dict, force: bool = False):
    """Создает или обновляет событие смены в календаре"""
    logger.debug(f"Обработка смены: {shift.get('employee_name')} (force={force})")
    try:
        start_dt = datetime.strptime(shift['start_time'], '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(shift['end_time'], '%Y-%m-%d %H:%M:%S')

        if not force:
            next_week_start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(weeks=1)
            next_week_end = next_week_start + timedelta(days=6)
            
            if not (next_week_start.date() <= start_dt.date() <= next_week_end.date()):
                logger.info(f"Пропуск смены {shift['employee_name']} - не следующая неделя")
                return

        summary = f"Смена: {shift['employee_name']}"
        description = shift.get('description', '')

        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': format_datetime_for_google(start_dt), 'timeZone': TIMEZONE},
            'end': {'dateTime': format_datetime_for_google(end_dt), 'timeZone': TIMEZONE}
        }

        existing = find_existing_event(service, summary, start_dt)

        if existing:
            if (existing['start'].get('dateTime') != event['start']['dateTime'] or
                existing['end'].get('dateTime') != event['end']['dateTime']):
                logger.debug(f"Обновление существующего события {existing['id']}")
                result = service.events().update(
                    calendarId=CALENDAR_ID,
                    eventId=existing['id'],
                    body=event
                ).execute()
                logger.info(f"Смена обновлена в календаре: {result.get('htmlLink')}")
            else:
                logger.info(f"Смена {shift['employee_name']} на {start_dt} не требует обновления")
        else:
            logger.debug("Создание нового события")
            result = service.events().insert(
                calendarId=CALENDAR_ID,
                body=event
            ).execute()
            logger.info(f"Смена добавлена в календарь: {result.get('htmlLink')}")
    except Exception as e:
        logger.error(f"Ошибка при обработке смены {shift.get('employee_name')}: {e}")
        raise
