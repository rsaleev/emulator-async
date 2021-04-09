
import struct
import asyncio
from src.api.shtrih.command import ShtrihCommand
from src.api.webkassa.commands import WebkassaClientCollection

class Withdraw(ShtrihCommand):
   
    _length = bytearray((0x05,))
    _command_code = bytearray((0x51,)) 
    _doc_number = struct.pack('<H',0)
        
    @classmethod
    async def handle(cls, payload:bytearray):
        await asyncio.gather(cls._process(payload), cls._dispatch())

    @classmethod
    async def _process(cls, payload:bytearray) -> bytearray:
        await WebkassaClientCollection.handle(payload, 0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._doc_number)
        return arr

    @classmethod
    async def _dispatch(cls)->None:
        pass

class Deposit(ShtrihCommand):

    _length = bytearray((0x05,))
    _command_code = bytearray((0x50,))
    _doc_number = struct.pack('<H',0)
        
    @classmethod
    async def handle(cls, payload:bytearray):
        await asyncio.gather(cls._process(payload), cls._dispatch())

    @classmethod
    async def _process(cls, payload):
        await WebkassaClientCollection.handle(payload, 1)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._doc_number)
        return arr

    @classmethod
    async def _dispatch(cls):
        pass
        


