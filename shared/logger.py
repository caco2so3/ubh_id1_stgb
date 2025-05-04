import logging
import os
import sys
from shared.config import LOG_FILE_PATH, LOG_LEVEL, LOGS_DIR

os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

logger = logging.getLogger('barhub')
logger.setLevel(getattr(logging, LOG_LEVEL, 'INFO'))

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.propagate = False
