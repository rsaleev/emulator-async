from os.path import normcase
import re
import asyncio
from src.api.printer.commands.querying import CheckLastOperation, ClearBuffer, EnsurePrintBuffer
from uuid import uuid4
from src import config
from src.api.shtrih import logger
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer, PrintDeferredBytes, PrintGraphicLines
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt
from typing import Pattern, NoReturn

class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload:bytearray) ->bytearray:
        try:
            #asyncio.create_task(cls._parse_custom_line(payload))
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
        
    class CustomHeader:
        PATTERN:Pattern = re.compile('|'.join(config['webkassa']['receipt']['header_regex']),re.IGNORECASE)

    @classmethod
    async def _parse_custom_line(cls, payload:bytearray)->None:
        try:
            line_to_print = bytes(payload[5:]).decode('cp1251')
            # check if line consists ticket number
            if config['webkassa']['receipt']['parse_ticket']:
                ticket = re.match(pattern=config['webkassa']['receipt']['ticket_regex'],  
                                string=line_to_print, 
                                flags=re.IGNORECASE)
                if ticket:
                    num = ticket.group(2)
                    await Receipt.create(uid=uuid4(), ticket=num)
            # check if line consists custom header data
            if not config['webkassa']['receipt']['header'] and config['webkassa']['receipt']['parse_header']:
                if re.match(pattern=cls.CustomHeader.PATTERN,
                            string=line_to_print):
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


