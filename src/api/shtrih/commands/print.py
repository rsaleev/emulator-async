import re
import asyncio
from typing import Tuple, Coroutine
from uuid import uuid4
from src import config
from typing import List
from src.api.printer.commands import PrintBytes, CutPresent, PrintBuffer
from src.api.shtrih import logger
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt


class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    def handle(cls, payload:bytearray) -> Tuple[Coroutine, Coroutine]:
        task_process = cls._process(payload)
        task_execute = cls._dispatch(payload)
        return task_process, task_execute


    @classmethod
    async def _process(cls, payload) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr

    @classmethod
    async def _dispatch(cls, payload:bytearray) -> None:
        await asyncio.gather(PrintBytes.handle(payload=payload[4:]), cls.__parse_custom_line(payload))
        
    @classmethod
    async def __parse_custom_line(cls, payload:bytearray) -> None:
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
    def handle(cls, payload:bytearray) -> Tuple[Coroutine, Coroutine]:
        task_process = cls._process(payload)
        task_execute = cls._dispatch(payload)
        return task_process, task_execute


    @classmethod
    async def _process(cls, payload:bytearray) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
        
    @classmethod
    async def _dispatch(cls, payload:bytearray) -> List[asyncio.Task]:
        tasks = []
        if config['printer']['text']['buffer']:
            tasks.append(asyncio.create_task(PrintBuffer.handle()))
        tasks.append(asyncio.create_task(CutPresent.handle()))
        return tasks
        

    