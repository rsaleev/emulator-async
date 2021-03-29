from src.api.printer.protocol import PrinterProto
from src.api.printer import logger
import os
import time
from src.api.printer.exceptions import DeviceIOError, DeviceConnectionError
from escpos.printer import Dummy
from src.api.printer.devices.impl import *
  



class Printer(PrinterProto):

    def __init__(self):
        super().__init__()
        if os.environ['PRINTER_TYPE'] == 'USB':
           self.__class__ = UsbPrinter
        self.buffer = Dummy()
  
    def _read(self, size):
        raise NotImplementedError

    def _write(self, data):
        raise NotImplementedError

    def discover(self):
        raise NotImplementedError

    def _disconnect(self):
        raise NotImplementedError

    def connect(self):
        while not self.device:
            try:
                self.discover()
            except DeviceConnectionError as e:
                logger.error(e)
                time.sleep(3)
            else:
                self.profile.profile_data['media']['width']['pixels'] = int(os.environ.get("PRINTER_PAPER_WIDTH", 540)) #type:ignore
                return self.device

    def reconnect(self):
        self.device=None
        self.connect()


    def disconnect(self):
        self.hw('INIT')
        self._disconnect()

    def read(self, size:int):
        while True:
            try:
                return self._read(size)
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue        

    def _raw(self, msg):
        while True:
            try:
                self._write(msg)
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue

    def write(self, data):
        while True:
            try:
                self._write(data)
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue

