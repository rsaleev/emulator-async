from src.utils.logger import SynchronousLogger
import os
from src import PATH

logger = SynchronousLogger(f'{PATH}/{os.environ.get("LOG_PATH")}/printer.log')