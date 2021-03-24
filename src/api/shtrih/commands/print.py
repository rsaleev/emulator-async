from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
import re
from uuid import uuid4
from src import config
from src.api.printer.commands import PrintBytes, CutPresent
from src.api.shtrih import logger
from src.db.models.receipt import Receipt
import asyncio


class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload:bytearray):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    async def dispatch(cls, payload:bytearray):
        task_parse = asyncio.create_task(cls._parse_custom_line(payload))
        task_print = PrintBytes.handle(payload=payload[4:])
        tasks = [task_parse, task_print]
        return tasks


    @classmethod
    async def _parse_custom_line(cls, payload:bytearray):
        try:
            line_to_print = bytes(payload[5:]).decode('cp1251')
            regex = config['webkassa']['receipt']['regex']
            line = re.match(regex, line_to_print, flags=re.IGNORECASE)
            if line:
                num = line.group(2)
                await Receipt.create(uid=uuid4(), ticket=num)
        except Exception as e:
            await logger.exception(e)
            
class Cut(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x25,))
   
    @classmethod
    async def handle(cls, payload:bytearray):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 
        

    @classmethod
    async def dispatch(cls, payload:bytearray) -> None:
        await CutPresent.handle()
    