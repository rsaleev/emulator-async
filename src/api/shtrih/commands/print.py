import re
import asyncio
from uuid import uuid4
from src import config
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt


class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload:bytearray) ->bytearray:
        try:
            await asyncio.gather(PrintBytes.handle(payload=payload[4:]),cls.__parse_custom_line(payload))
        except:
            cls.set_error(200) # printer error: no connection or no signal from sensors
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
        
    @classmethod
    async def __parse_custom_line(cls, payload:bytearray) -> None:
        line_to_print = bytes(payload[5:]).decode('cp1251')
        regex = config['webkassa']['receipt']['regex']
        line = re.match(regex, line_to_print, flags=re.IGNORECASE)
        if line:
            num = line.group(2)
            await Receipt.create(uid=uuid4(), ticket=num)
        
class Cut(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x25,))
   
    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        try:
            if config['printer']['text']['buffer']:
                await PrintBuffer.handle()
            await CutPresent.handle()
        except:
            cls.set_error(200) # printer error: no connection or no signal from sensors
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
 