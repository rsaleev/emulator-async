from abc import ABC, abstractclassmethod
import struct

class ShtrihCommand:
    _password = bytearray((0x30,))
    _error_code = bytearray((0x00,))

    @classmethod
    def set_error(cls, v:int) ->None:
        cls._error_code = struct.pack('<B', v)

    @classmethod
    def set_password(cls, v:int)->None:
        cls._password = struct.pack('<B', v)


class ShtrihCommandInterface(ABC):
    
    @abstractclassmethod
    def handle():   
        pass

