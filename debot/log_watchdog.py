import os
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from shared.config import LOG_FILE_PATH, LOGS_DIR
from shared.logger import logger

class LogFileHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы для лог-файла"""
    
    def __init__(self):
        self.last_position = 0
        self.check_file_exists()
    
    def check_file_exists(self):
        """Проверяет существование лог-файла и создает его при необходимости"""
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
            logger.info(f"Создана директория логов: {LOGS_DIR}")
            
        if not os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(f"=== Лог-файл создан {datetime.now().isoformat()} ===\n")
            logger.info(f"Создан новый лог-файл: {LOG_FILE_PATH}")
    
    def on_modified(self, event):
        """Обрабатывает событие изменения файла"""
        if event.src_path == LOG_FILE_PATH:
            self.process_new_logs()
    
    def process_new_logs(self):
        """Обрабатывает новые записи в лог-файле"""
        try:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_logs = f.read()
                if new_logs:
                    self.analyze_logs(new_logs)
                self.last_position = f.tell()
        except Exception as e:
            logger.error(f"Ошибка при чтении лог-файла: {e}")
    
    def analyze_logs(self, logs):
        """Анализирует новые логи на наличие важных событий или ошибок"""
        for line in logs.splitlines():
            if "ERROR" in line or "CRITICAL" in line:
                logger.warning(f"Обнаружена критическая запись в логах: {line}")
            elif "WARNING" in line:
                logger.info(f"Обнаружено предупреждение: {line}")

def run_watchdog():
    """Запускает отслеживание лог-файла"""
    logger.info("Запуск системы мониторинга логов...")
    
    try:
        event_handler = LogFileHandler()
        observer = Observer()
        observer.schedule(event_handler, path=LOGS_DIR, recursive=False)
        observer.start()
        logger.info("Мониторинг лог-файла запущен успешно")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("Мониторинг логов остановлен пользователем")
        
        observer.join()
    except Exception as e:
        logger.error(f"Ошибка при запуске мониторинга логов: {e}")

if __name__ == "__main__":
    run_watchdog()
