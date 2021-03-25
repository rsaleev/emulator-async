
import struct
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface


class SerialNumber(ShtrihCommand, ShtrihCommandInterface):
   
        
    _length = bytearray((0x17,))# B[1] LEN - 1 byte
    _command_code = bytearray((0xFF,0x02,)) #B[2] - 2 byte
    _fn_number = struct.pack('<16B',*[0x30]*16)
    
    @classmethod
    async def handle(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._fn_number)
        return arr

    @classmethod
    async def dispense(cls):
        pass


        

