import toml
import os
from dotenv import load_dotenv
from src.utils.logger import CustomLogger

path = os.path.abspath(os.getcwd())
load_dotenv(f'{path}/webcassa.env')
#logger = CustomLogger(f"{path}/logs/application.log")
config = toml.load(f'{path}/config.toml')