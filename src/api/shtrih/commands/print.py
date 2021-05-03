import re
import asyncio
from src.api.printer.commands.querying import ClearBuffer, EnsurePrintBuffer
from uuid import uuid4
from src import config
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer, PrintDeferredBytes, PrintGraphicLines
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
        
    class NoChangeHeader:
        line1=r"^Невыданная сдача\W+"
        line2=r"^\W+Банкноты\W+\d+\W+\d+\w+"
        line3=r"^\W+Монеты\W+\d+\W+\d+\w+"
        line4=r"^\W+Недоступно\W+\d+\W+\d+\w+"
        lines = [line1, line2, line3, line4]

    @classmethod
    async def _parse_custom_line(cls, payload:bytearray) -> None:
        line_to_print = bytes(payload[5:]).decode('cp1251')
        # check if line consists ticket number
        ticket = re.match(pattern=config['webkassa']['receipt']['regex'],  
                        string=line_to_print, 
                        flags=re.IGNORECASE)
        if ticket:
            num = ticket.group(2)
            await Receipt.create(uid=uuid4(), ticket=num)
        # check if line consists payment w/o change data
        for line in cls.NoChangeHeader.lines:
            data = re.match(line,line_to_print)
            if data:
                # store 
                await PrintDeferredBytes.append(payload) 
                
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
            # wait for execution:
            # if error occured -> return 0x200
            await PrintBuffer.handle()
            if not config['printer']['ensure_printed']:
                await ClearBuffer.handle()
            else:
                asyncio.create_task(EnsurePrintBuffer.handle())
        except:
            cls.set_error(200) # printer error: no connection or no signal from sensors
        else:
            cls.set_error(0)
        finally:
            await CutPresent.handle()
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
 