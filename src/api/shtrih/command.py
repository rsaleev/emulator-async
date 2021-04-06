from abc import ABC, abstractclassmethod
import struct

class ShtrihCommand:
    _password = bytearray((0x30,))
    _error_code = bytearray((0x00,))

    @classmethod
    def set_error(cls, v:int) ->None:
        cls._error_code = bytearray((v,))

    @classmethod
    def set_password(cls, v:int)->bytes:
        return struct.pack('<B', v)


class ShtrihCommandInterface(ABC):
    
    @abstractclassmethod
    async def handle():
        """
        Method for preparing response on command:
        """
        pass

    @abstractclassmethod
    async def _process():
        pass

    @abstractclassmethod
    async def _dispatch():
        pass

