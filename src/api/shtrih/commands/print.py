import struct
from src.protocols.shtrih.command import ShtrihCommand
from src.db.models.receipt import Receipt
from src.devices.printer import PrinterDeviceProxy
import re
from functools import partial
import asyncio

class PrinterNotDefined(Exception):
    pass

class PrinterPrintingError(Exception):
    pass

class PrintDefaultLine(ShtrihCommand):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        tasks = []
        tasks.append(cls._device.write())
    
    @classmethod
    async def dispense(cls, payload:bytearray):
        task = PrinterDeviceProxy.PrintBytes.handle(data) #type: ignore 
        return task



    @classmethod
    def _line_parser(cls, payload:bytearray):
        line_to_print = bytes(payload).decode('cp1251')
        # CHECK FOR RECEIPT ITEM
        regex = r'(code\W\W\W|код\W\W\W)(\d*)'
        line = re.search(regex, line_to_print, flags=re.IGNORECASE)
        if line:
            num = line.group(2)
            return num 
       

class Cut(ShtrihCommand):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x25,))
   

    @classmethod
    def handle(cls) -> bytearray:
       
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr

    @classmethod
    def dispense(cls) -> None:
        pass


class GraphicLine(ShtrihCommand):

    _length =  bytearray((0x03,))
    _command_code = bytearray((0xC5,))

    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr

    @classmethod
    def dispense(cls)->None:
        pass
   


