from abc import ABC, abstractclassmethod
from typing import Any


class Device(ABC):

    @abstractclassmethod
    async def connect():
        pass

    @abstractclassmethod
    async def reconnect():
        pass
    
    @abstractclassmethod
    async def disconnect():
        pass

    @abstractclassmethod
    async def _read(cls, *args:Any, **kwargs):
        pass


    @abstractclassmethod
    async def _write(cls,*args:Any, **kwargs):
        pass
