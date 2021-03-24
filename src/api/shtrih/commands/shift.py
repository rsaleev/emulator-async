from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.webkassa.commands import WebkassaClientCloseShift
from src.db.models import States, Shift
from datetime import datetime
import asyncio

class OpenShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x01,))
    _command_code = bytearray((0xE8,))
    
    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray: 
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    async def dispatch(cls, payload:bytearray):
        tasks = [] 
        tasks.append(States.filter(id=1).update(mode=2))
        tasks.append(Shift.filter(id=1).update(open_date=datetime.now(), total_docs=0))
        await asyncio.gather(*tasks)

class CloseShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x05,))
    _command_code = bytearray((0xFF,0x43))

    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        return arr
        
    
    @classmethod
    async def dispense(cls, payload:bytearray):
        tasks = [] 
        tasks.append(States.filter(id=1).update(mode=2))
        tasks.append(Shift.filter(id=1).update(open_date=datetime.now(), total_docs=0))
        tasks.append(WebkassaClientCloseShift.handle())
        await asyncio.gather(*tasks)

        