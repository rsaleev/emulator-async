import asyncio
from typing import Coroutine, List, Tuple
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.webkassa.commands import WebkassaClientXReport, WebkassaClientZReport

class ZReport(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x41,))
            
    @classmethod
    async def handle(cls, payload:bytearray):
        await WebkassaClientZReport.handle()
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
    def handle(cls, payload:bytearray) -> Tuple[Coroutine, Coroutine]:
        task_process = cls._process(payload)
        task_execute = cls._dispatch()
        return task_process, task_execute
        
    @classmethod
    async def _process(cls, payload:bytearray) -> bytearray:   
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
      
    @classmethod
    async def _dispatch(cls) -> None:
        await WebkassaClientXReport.handle()
      
        
