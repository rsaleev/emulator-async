from abc import ABC, abstractclassmethod
import struct
from src.api.shtrih.commands import root_logger

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
        Method for preparing response on comman:
        """
        pass


    @abstractclassmethod
    async def dispatch():
        """
        Method for processing data to external systems: API, DB, etc.
        """
        pass
