
import struct
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.shtrih.device import Paykiosk

class SerialNumber(ShtrihCommand, ShtrihCommandInterface, Paykiosk):
   
        
    _length = bytearray((0x17,))# B[1] LEN - 1 byte
    _command_code = bytearray((0xFF,0x02,)) #B[2] - 2 byte
    _fn_number = struct.pack('<16B',*[0x30]*16)
    
    @classmethod
    async def handle(cls, payload):
        await cls._process()


    @classmethod
    async def _process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._fn_number)
        await Paykiosk()._transmit(arr)

    @classmethod
    async def _dispatch(cls):
        pass


        


