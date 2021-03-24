import os
from src.utils.logger import AsynchronousLogger
from dotenv import load_dotenv
import toml

load_dotenv(f'{os.path.abspath(os.getcwd())}/webcassa.env')
config = toml.load(f'{os.environ.get("CONFIG")}')
logger = AsynchronousLogger(f'{os.environ.get("LOG_PATH")}/emulator.log')




