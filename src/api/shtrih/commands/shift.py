import struct
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.state import States
from src.db.models.shift import Shift
from datetime import datetime
import asyncio

class OpenShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x01,))
    _command_code = bytearray((0xE8,))
    
    @classmethod
    async def handle(cls, payload:bytearray) -> None:
        tasks = []

        
    @classmethod
    async def process(cls):    
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        crc = cls.crc_calc(arr)
        arr.extend(crc)
        output = bytearray()
        output.extend(cls.STX)
    
    @classmethod
    async def dispense(cls):
        tasks = [] 
        tasks.append(States.filter(id=1).update(mode=2))
        tasks.append(Shift.filter(id=1).update(open_date=datetime.now(), total_docs=0))
        await asyncio.gather(*tasks)

class CloseShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x05,))
    _command_code = bytearray((0xFF,0x43))
    

    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls):
        pass