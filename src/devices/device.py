from abc import ABC, abstractclassmethod, abstractmethod


class AbstractDevice(ABC):

    @abstractclassmethod
    async def discover(cls,*args, **kwargs):
        pass

    @abstractclassmethod
    async def connect(cls,*args, **kwargs):
        pass

    @abstractclassmethod
    async def reconnect(cls):
        pass

    @abstractclassmethod
    async def disconnect(cls, *args, **kwargs):
        pass

    @abstractclassmethod
    async def read(cls, *args, **kwargs):
        pass

    @abstractclassmethod
    async def write(cls, *args, **kwargs):
        pass

    
class AbstractBuffer(ABC):
    @abstractmethod
    def empty():
        pass

    
