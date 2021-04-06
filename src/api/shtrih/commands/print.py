import re
import asyncio
from uuid import uuid4
from src import config
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer
from src.api.shtrih import logger
from src.api.shtrih.device import Paykiosk
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt


class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface, Paykiosk):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    async def handle(cls, payload:bytearray):
        task_write = cls._process(payload)
        task_execute = cls._dispatch(payload)
        task_optional = cls._parse_custom_line(payload)
        if config['webkassa']['receipt']['parse']:
            await asyncio.gather(task_write, task_execute, task_optional)
        else:
            await asyncio.gather(task_write, task_execute)

    @classmethod
    async def _process(cls, payload):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        await Paykiosk()._transmit(arr)

    @classmethod
    async def _dispatch(cls, payload:bytearray):
        await PrintBytes.handle(payload=payload[4:])
        
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
        task_write = cls._process(payload)
        task_execute = cls._dispatch(payload)
        await asyncio.gather(task_write, task_execute)

    @classmethod
    async def _process(cls, payload:bytearray):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        await Paykiosk()._transmit(arr)
        
    @classmethod
    async def _dispatch(cls, payload:bytearray) -> None:
        if config['printer']['text']['buffer']:
            await PrintBuffer.handle()
        await CutPresent.handle()
        

    