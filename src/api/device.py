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
    async def read(cls, *args:Any, **kwargs):
        pass


    @abstractclassmethod
    async def write(cls,*args:Any, **kwargs):
        pass

class DeviceImpl(ABC):

    @abstractclassmethod
    def _open(cls, *args:Any, **kwargs):
        pass

    @abstractclassmethod
    def _close(cls, *args:Any, **kwargs):
        pass

    @abstractclassmethod
    def _read(cls, *args:Any, **kwargs):
        pass

    @abstractclassmethod
    def _write(cls,*args:Any, **kwargs):
        pass

class DeviceConnectionError(Exception):
    pass

class DeviceIOError(Exception):
    pass