from asyncio.tasks import create_task
import logging 
import os
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter

from typing import Any, Optional, Dict
import asyncio
from functools import partial

class MyFormatter(logging.Formatter):

    def __init__(self):
        super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style='%')  
    
    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = "DEBUG: %(asctime)s LINE:%(lineno)d FUNC:%(funcName)s MSG:%(msg)s"

        elif record.levelno == logging.INFO:
            self._style._fmt = "INFO: %(asctime)s %(msg)s"

        elif record.levelno == logging.ERROR:
            self._style._fmt = "ERROR: %(asctime)s %(msg)s"

        elif record.levelno == logging.WARNING:
            self._style._fmt = "WARNING: %(asctime)s %(msg)s"

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result


class CustomLogger(logging.Logger):

    def __init__(self, filename='test.log', name:str =__name__):
        self._loop = asyncio.get_event_loop()
        super().__init__(name, getattr(logging, os.environ.get("LOG_LEVEl", 'INFO')))
        my_formatter = MyFormatter()
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(my_formatter)
        self.addHandler(streamHandler)
        if filename:
            fileHandler = TimedRotatingFileHandler(filename, when="midnight",
                                       interval=1,
                                       backupCount=31)
            fileHandler.setFormatter(my_formatter)
            self.addHandler(fileHandler)
        self.setLevel(self.level)


   