from src.utils.logger import AsynchronousLogger
import os
from src import PATH

logger = AsynchronousLogger(f'{PATH}/{os.environ.get("LOG_PATH")}/emulator.log')


