import struct
from src.protocols.shtrih.command import ShtrihCommand, ShtrihCommandInterface
class PrinterNotDefined(Exception):
    pass

class PrinterPrintingError(Exception):
    pass

class PrintDefaultLine(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x17,))
            
    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls, printer, data:bytearray):
        printer.print_bytes(data[5:], font='a')


    @classmethod(cls, )
       

class Cut(ShtrihCommand,ShtrihCommandInterface):

    _length = bytearray((0x03,))
    _command_code = bytearray((0x25,))
   

    @classmethod
    def handle(cls) -> bytearray:
       
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr

    @classmethod
    def dispense(cls) -> None:
        pass


class GraphicLine(ShtrihCommand, ShtrihCommandInterface):

    _length =  bytearray((0x03,))
    _command_code = bytearray((0xC5,))

    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)

    @classmethod
    def dispense(cls)->None:
        pass
   


