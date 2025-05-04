import gspread
from datetime import datetime, timedelta
import logging
import json
import os
import re
from shared.config import SPREADSHEET_URL, GOOGLE_CREDS_PATH, SHIFTS_DB_PATH

logger = logging.getLogger('barhub')

def get_current_week_range():
    """Получает диапазон дней текущей недели"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return {
        'range': f"{monday.day}-{sunday.day}",
        'start': monday,
        'end': sunday
    }

def is_current_week(header_text, worksheet):
    """Проверяет, соответствует ли заголовок текущей неделе"""
    current_week = get_current_week_range()
    
    def extract_numbers(text):
        if not text:
            return None
        parts = text.strip().split('-')
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            return [int(p) for p in parts]
        return None
    
    numbers = extract_numbers(header_text)
    if numbers:
        if f"{numbers[0]}-{numbers[1]}" == current_week['range']:
            return True
            
    try:
        header_values = worksheet.batch_get(['C2:I2'])[0]
        if header_values and header_values[0]:
            header_numbers = [int(cell) for cell in header_values[0] 
                            if str(cell).strip().isdigit()]
            if len(header_numbers) >= 2:
                sheet_week = f"{min(header_numbers)}-{max(header_numbers)}"
                if sheet_week == current_week['range']:
                    return True
    except Exception as e:
        logger.warning(f"Не удалось проверить диапазон C2:I2: {str(e)}")
    
    return False

def extract_shift_name(time_string):
    """Извлекает название бара из строки времени смены, типа '18-2 брудер'"""
    if not time_string:
        return "unknown"
    match = re.search(r'\b([а-яА-Яa-zA-Z]+)$', time_string.strip())
    return match.group(1).lower() if match else "unknown"

def get_shifts_from_spreadsheet(force=False):
    """Получает данные о сменах из Google таблицы с группировкой по сотрудникам"""
    try:
        logger.info("Подключение к Google Sheets...")
        gc = gspread.service_account(filename=GOOGLE_CREDS_PATH)
        spreadsheet = gc.open_by_url(SPREADSHEET_URL)
        worksheets = spreadsheet.worksheets()
        worksheet = worksheets[-1]
        current_week = get_current_week_range()

        if not force and is_current_week(worksheet.title, worksheet):
            logger.info(f"Лист {worksheet.title} — текущая неделя, пропускаем")
            return {}

        values = worksheet.get_values()
        if not values:
            logger.warning("Таблица пуста")
            return {}

        logger.info(f"Получено {len(values)} строк данных")

        employee_shifts = {}

        for row_num, row in enumerate(values[1:], start=2):
            if len(row) >= 3:
                name = row[0].strip()
                start = row[1].strip()
                end = row[2].strip()
                desc = row[3].strip() if len(row) > 3 else ""

                shift_entry = {
                    "start_time": start,
                    "end_time": end,
                    "shift_name": extract_shift_name(start),
                    "description": desc
                }

                if name:
                    if name not in employee_shifts:
                        employee_shifts[name] = []
                    employee_shifts[name].append(shift_entry)
                else:
                    logger.warning(f"Пустое имя в строке {row_num}")

        logger.info(f"Группировка завершена: {len(employee_shifts)} сотрудников")
        return employee_shifts

    except Exception as e:
        logger.error(f"Ошибка при чтении данных из таблицы: {str(e)}")
        raise

def sync_shifts_to_json(force=False):
    """Сохраняет сгруппированные смены в локальный JSON-файл"""
    try:
        shifts_by_employee = get_shifts_from_spreadsheet(force=force)
        if shifts_by_employee:
            with open(SHIFTS_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(shifts_by_employee, f, ensure_ascii=False, indent=2)
            logger.info(f"Смены успешно сохранены в {SHIFTS_DB_PATH}")
        else:
            logger.info("Нет новых смен для сохранения")
        return shifts_by_employee
    except Exception as e:
        logger.error(f"Ошибка при синхронизации смен: {str(e)}")
        raise
