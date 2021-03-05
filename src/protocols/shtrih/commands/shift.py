import struct
from src.protocols.shtrih.command import ShtrihCommand, ShtrihCommandInterface

class OpenShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x01,))
    _command_code = bytearray((0xE8,))
    
    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls):
        pass

class CloseShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x05,))
    _command_code = bytearray((0xFF,0x43))
    

    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls):
        pass