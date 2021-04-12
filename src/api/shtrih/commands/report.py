import asyncio
from typing import Coroutine, List, Tuple
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.webkassa.commands import WebkassaClientXReport, WebkassaClientZReport

class ZReport(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x41,))
            
    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        try:
            await WebkassaClientZReport.handle()
        except:
            cls.set_error(32)
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
       
class XReport(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x40,))
            
    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        try:
            await WebkassaClientXReport.handle()
        except:
            cls.set_error(32)
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
   
      
        
