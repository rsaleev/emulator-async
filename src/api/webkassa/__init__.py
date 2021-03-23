from src.utils.logger import AsynchronousLogger
import os

path = os.path.abspath(os.getcwd())
logger = AsynchronousLogger(f"{path}/logs/webkassa.log")
