
import struct
from src.api.shtrih.command import ShtrihCommand
from src.api.webkassa.commands import WebkassaClientCollection

class Withdraw(ShtrihCommand):
   
    _length = bytearray((0x05,))
    _command_code = bytearray((0x51,)) 
    _doc_number = struct.pack('<H',0)
        
    @classmethod
    async def handle(cls, payload:bytearray):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._doc_number)
        return bytes(arr)

    @classmethod
    async def dispatch(cls, payload:bytearray):
        await WebkassaClientCollection.handle(payload, 0)

class Deposit(ShtrihCommand):

    _length = bytearray((0x05,))
    _command_code = bytearray((0x50,))
    _doc_number = struct.pack('<H',0)
        
    @classmethod
    async def handle(cls, payload:bytearray):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._doc_number)
        return bytes(arr)

    @classmethod
    async def dispatch(cls, payload:bytearray):
        await WebkassaClientCollection.handle(payload, 1)
        


