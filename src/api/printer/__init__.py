from src.utils.logger import SynchronousLogger
import os

logger = SynchronousLogger(f'{os.environ.get("LOG_PATH")}/webcassa.log')