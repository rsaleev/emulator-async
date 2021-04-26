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
    async def _read(cls, *args:Any, **kwargs):
        pass

    @abstractclassmethod
    async def _write(cls,*args:Any, **kwargs):
        pass

    @abstractclassmethod
    async def _connect(cls):
        pass

    @abstractclassmethod
    async def _disconnect(cls):
        pass


class DeviceConnectionError(Exception):
    pass

class DeviceIOError(Exception):
    pass

class DeviceTimeoutError(Exception):
    pass