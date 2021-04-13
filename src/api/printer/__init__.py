from src.utils.logger import SynchronousLogger, AsynchronousLogger
import os
from src import PATH

logger = SynchronousLogger(f'{PATH}/logs/printer.log')
async_logger = AsynchronousLogger(f'{PATH}/logs/printer.log')