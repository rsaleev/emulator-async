from abc import ABC, abstractclassmethod
import struct
from typing import Callable
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
    def handle():
        """handle 

        returns array of asyncio.Tasks
        """
    
        pass

    @abstractclassmethod
    def _process():
        """_process 

        returns result of processing
        """
        pass

    @abstractclassmethod
    def _dispatch():
        """_dispatch 

        returns execution logic
        """
        pass
