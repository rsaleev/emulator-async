from aiologger.handlers.files import AsyncTimedRotatingFileHandler, RolloverInterval
from aiologger.formatters.base import Formatter
from tempfile import NamedTemporaryFile
import logging
from logging.handlers import TimedRotatingFileHandler
import aiologger
import os

class CustomAsyncFormatter(Formatter):

    def __init__(self):
        super().__init__(fmt="%(levelname)s %(asctime)s %(message)s")  
    
    def format(self, record):
        format_orig = self._style._fmt
        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = "%(levelname)s %(asctime)s LINE:%(lineno)d FUNC:%(funcName)s MSG:%(message)s"

        elif record.levelno == logging.INFO:
            self._style._fmt = "%(levelname)s %(asctime)s %(message)s"

        elif record.levelno == logging.ERROR:
            self._style._fmt = "%(levelname)s %(asctime)s %(message)s"

        elif record.levelno == logging.WARNING:
            self._style._fmt = "%(levelname)s %(asctime)s %(message)s"

        # Call the original formatter class to do the grunt work
        result = super().format(record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig
        return result


class AsynchronousLogger(aiologger.Logger):
    def __init__(self,  filename:str,name:str = __name__):
        super().__init__(name=name, level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')))
        temp_file = NamedTemporaryFile()
        temp_file.name = filename #type: ignore
        handler = AsyncTimedRotatingFileHandler(filename=temp_file.name,
                                                backup_count=14,
                                                interval=1,
                                                when=RolloverInterval.MIDNIGHT,
                                                encoding='utf8')
        
        custom_formatter = CustomAsyncFormatter()
        handler.formatter = custom_formatter
        self.add_handler(handler)



