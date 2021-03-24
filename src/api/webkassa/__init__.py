from src.utils.logger import AsynchronousLogger
import os

logger = AsynchronousLogger(f'{os.environ.get("LOG_PATH")}/webcassa.log')