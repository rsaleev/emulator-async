import os
from src.utils.logger import AsynchronousLogger
from dotenv import load_dotenv
import toml

PATH = os.path.abspath(os.getcwd())
load_dotenv(f'{PATH}/webcassa.env')
config = toml.load(f'{PATH}/config.toml')
print(config['printer'])
logger = AsynchronousLogger(f'{PATH}/logs/application.log')




