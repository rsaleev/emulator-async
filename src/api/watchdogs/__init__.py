import os 
from src.utils.logger import AsynchronousLogger


PATH = os.path.abspath(os.getcwd())


logger = AsynchronousLogger(f'{PATH}/logs/watchdogs.log')
