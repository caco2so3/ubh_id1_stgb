import os
import json
import datetime
import logging
from shared.config import GOOGLE_CREDS_PATH, CALENDAR_ID, TIMEZONE
from shared.logger import logger
from shared.sheet_parser import sync_shifts_to_json
from .uploader import upload_shifts_to_calendar
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Создает и возвращает сервис Google Calendar API"""
    logger.debug(f"Инициализация сервиса Google Calendar с учетными данными из {GOOGLE_CREDS_PATH}")
    
    if not os.path.exists(GOOGLE_CREDS_PATH):
        logger.error(f"Не найден файл авторизации: {GOOGLE_CREDS_PATH}")
        raise FileNotFoundError("Google credentials file not found")

    try:
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar API авторизован успешно")
        return service
    except Exception as e:
        logger.error(f"Ошибка при инициализации сервиса календаря: {str(e)}")
        raise

def add_event(summary: str, description: str, start_time: datetime.datetime, 
              end_time: datetime.datetime, calendar_id: str = CALENDAR_ID) -> dict:
    """Добавляет событие в календарь"""
    logger.debug(f"Добавление события '{summary}' на {start_time}")
    
    service = get_calendar_service()
    
    try:
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': TIMEZONE},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': TIMEZONE},
        }

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.info(f"Событие успешно добавлено в календарь: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as e:
        logger.error(f"Ошибка API при добавлении события: {e.status_code} - {e.error_details}")
        raise
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при добавлении события: {str(e)}")
        raise

async def run_uploader():
    """Асинхронная функция для тестовой загрузки смен"""
    logger.info("Запуск тестового загрузчика смен...")
    
    try:
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=8)
        
        summary = "Тестовая смена"
        description = "Тестовое событие для проверки работы календаря"

        created_event = add_event(
            summary=summary, 
            description=description, 
            start_time=start_time, 
            end_time=end_time
        )
        logger.info(f"Тестовое событие успешно создано: {created_event.get('id')}")
        
    except Exception as e:
        logger.error(f"Ошибка при тестовой загрузке смены: {str(e)}")
        raise
    finally:
        logger.info("Завершение работы тестового загрузчика")

def load_shifts(force=False):
    """Загружает смены и синхронизирует их с календарем"""
    logger.info(f"Запуск загрузки смен (force={force})")
    
    try:
        shifts = sync_shifts_to_json()
        
        if not shifts:
            logger.info("Нет новых смен для синхронизации (возможно это текущая неделя)")
            return
            
        if shifts and (force or len(shifts) > 0):
            upload_shifts_to_calendar(shifts)
            logger.info("Смены успешно загружены в календарь")
    except Exception as e:
        logger.error(f"Ошибка при загрузке смен: {str(e)}")
        raise
    
    logger.info("Загрузка смен успешно завершена")
