import re
import asyncio
from uuid import uuid4
from src import config
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer, ClearBuffer, PrintGraphicLines
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt


class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload:bytearray) ->bytearray:
        try:
            await PrintBytes.handle(payload=payload[4:])
            asyncio.ensure_future(cls._parse_custom_line(payload))
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
    async def _parse_custom_line(cls, payload:bytearray) -> None:
        line = re.match(pattern=config['webkassa']['receipt']['regex'],  
                        string=bytes(payload[5:]).decode('cp1251'), 
                        flags=re.IGNORECASE)
        if line:
            num = line.group(2)
            await Receipt.create(uid=uuid4(), ticket=num)
            if not config['webkassa']['receipt']['header']:
                asyncio.ensure_future(ClearBuffer.handle())

class PrintOneDimensionalBarcode(ShtrihCommand, ShtrihCommandInterface):
    _length =  bytearray((0x03,))
    _command_code = bytearray((0xC5,))

    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        try:
            await PrintGraphicLines.handle(payload)
        except:
            cls.set_error(57)
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr


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
 