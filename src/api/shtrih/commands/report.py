
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.webkassa.commands import WebkassaClientXReport, WebkassaClientZReport
from src.api.printer.commands import PrintXML, CutPresent
from src.api.webkassa.exceptions import UnresolvedCommand


class ZReport(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x41,))
            
    @classmethod
    async def handle(cls, payload:bytearray) ->bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr


    @classmethod
    async def dispatch(cls):
        doc = await WebkassaClientZReport.handle()
        if doc:
            await PrintXML.handle(doc)
            await CutPresent.handle()


class XReport(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x40,))
            
    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
      
    @classmethod
    async def dispatch(cls, payload:bytearray):
        doc = await WebkassaClientXReport.handle()
        if doc:
            await PrintXML.handle(doc) 
            await CutPresent.handle()
        else:
            raise UnresolvedCommand("Couldn't print XReport document, no data for template")
        
