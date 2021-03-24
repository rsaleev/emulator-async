import os
from src.utils.logger import AsynchronousLogger
from dotenv import load_dotenv
import toml

path = os.path.abspath(os.getcwd())

if not os.path.isdir(f'{path}/logs'):
    os.mkdir(f'{path}/logs')

load_dotenv(f'{path}/webcassa.env')
config = toml.load(f'{path}/config.toml')
logger = AsynchronousLogger(f'{path}/logs/appliaction.log')




