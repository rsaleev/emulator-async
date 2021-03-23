
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.webkassa.commands import WebkassaClientCloseShift, WebkassaClientXReport, WebkassaClientZReport
from src.api.printer.commands import PrintXML, CutPresent
import asyncio
from src.api.shtrih import logger

class ZReport(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x41,))
            
    @classmethod
    async def handle(cls, payload) -> None:
        tasks = [cls.process(), cls.dispatch()]
        await asyncio.gather(*tasks)

    @classmethod
    async def process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        await cls.send(arr)


    @classmethod
    async def dispatch(cls):
        doc = await WebkassaClientZReport.handle()
        if doc:
            await PrintXML.handle(doc, buffer=False)
            await CutPresent.handle()


class XReport(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x40,))
            
    @classmethod
    async def handle(cls, payload) -> None:
        tasks = [cls.process(), cls.dispatch()]
        await asyncio.gather(*tasks)

    @classmethod
    async def process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        await cls.send(arr)
      
    @classmethod
    async def dispatch(cls):
        doc = await WebkassaClientXReport.handle()
        if doc:
            await PrintXML.handle(doc, buffer=False)
            await CutPresent.handle()
