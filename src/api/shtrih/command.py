from abc import ABC, abstractclassmethod
import struct
from src.api.shtrih.device import ShtrihProxyDevice
from src.api.shtrih.protocol import ShtrihProto
from src.api.shtrih import logger


class ShtrihCommand(ShtrihProxyDevice,ShtrihProto):
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
        Method for handling incoming data:
        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError


    @abstractclassmethod
    async def process():
        """
        Method for handling incoming data:
        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    



    @abstractclassmethod
    async def dispense():
        """
        Method for processing data in external systems: API, DB, etc.

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError
