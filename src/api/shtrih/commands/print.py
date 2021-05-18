import re
import asyncio
from src.api.printer.commands.querying import CheckLastOperation, ClearBuffer, EnsurePrintBuffer
from uuid import uuid4
from src import config
from src.api.shtrih import logger
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer, PrintDeferredBytes, PrintGraphicLines
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt


class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload:bytearray) ->bytearray:
        try:
            asyncio.create_task(cls._parse_custom_line(payload))
            await PrintBytes.handle(payload=payload[4:])
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
        
    class CustomHeader:
        # No change
        line1=r"^Невыданная сдача\W+"
        line2=r"^\W+Банкноты\W+\d+\W+\d+\w+"
        line3=r"^\W+Монеты\W+\d+\W+\d+\w+"
        line4=r"^\W+Недоступно\W+\d+\W+\d+\w+"
        # POS
        line5=r"^Время операции:\W+\w+\W+\w+\W+\w+\W+\w+\W+\w+\W+\w+"
        line6=r"^Тип операции:\W+\w+"
        line7=r"^Сумма:\W+\d+\W+\w+\W+"
        line8=r"^Номер карты:\W+\w+\w+\W+\w+"
        line9=r"^RRN:\W+\w+"
        line10=r"^RC:\W+\w+"
        line11=r"^Auth:\W+\w+"
        line12=r"^Application:\W+\w+\W+\w+"
        line13=r"^AID:\W+\w+"
        line14=r"^TC:\W+\w+"
        lines = [line1, line2, line3, line4, line5, line6, line7, line8, line9, line10, line11, line12, line13, line14]


    @classmethod
    async def _parse_custom_line(cls, payload:bytearray) -> None:
        try:
            line_to_print = bytes(payload[5:]).decode('cp1251')
            # check if line consists ticket number
            ticket = re.match(pattern=config['webkassa']['receipt']['regex'],  
                            string=line_to_print, 
                            flags=re.IGNORECASE)
            if ticket:
                num = ticket.group(2)
                await Receipt.create(uid=uuid4(), ticket=num)
            # check if line consists payment w/o change data
            for line in cls.CustomHeader.lines:
                data = re.match(pattern=line,string=line_to_print,flags=re.IGNORECASE)
                if data:
                    # store 
                    await PrintDeferredBytes.append(payload) 
        except Exception as e:
            logger.error(e)
                
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
        # wait for execution:
        # if error occured -> return 0x200
        await PrintBuffer.handle()
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        if config['printer']['text']['ensure_printed']:
            try:
                await asyncio.sleep(config['printer']['text']['ensure_printed_delay'])
                await CheckLastOperation.handle()
            except:
                cls.set_error(200)
                asyncio.create_task(EnsurePrintBuffer.handle())
            else:
                cls.set_error(0)
                await ClearBuffer.handle()
                await CutPresent.handle()
        else:
            cls.set_error(0)
            await CutPresent.handle()
            await ClearBuffer.handle()
        return arr


