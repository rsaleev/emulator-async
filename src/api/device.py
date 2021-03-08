from abc import ABC, abstractclassmethod, abstractmethod
from typing import Callable

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


class ProxyDevice:
    """
    Create a proxy or placeholder for another object.
    """
    __slots__ = ('obj', '_callbacks')

    def __init__(self):
        self._callbacks = []
        self.initialize(None)

    def initialize(self, obj):
        self.obj = obj
        for callback in self._callbacks:
            callback(obj)

    def attach_callback(self, callback):
        self._callbacks.append(callback)
        return callback

    def passthrough(method):
        def inner(self, *args, **kwargs):
            if self.obj is None:
                raise AttributeError('Cannot use uninitialized Proxy.')
            return getattr(self.obj, method)(*args, **kwargs) #type: ignore
        return inner

    # Allow proxy to be used as a context-manager.
    __enter__ = passthrough('__enter__') #type: ignore
    __exit__ = passthrough('__exit__') #type: ignore

    def __getattr__(self, attr):
        if self.obj is None:
            raise AttributeError('Cannot use uninitialized Proxy.')
        return getattr(self.obj, attr)

    def __setattr__(self, attr, value):
        if attr not in self.__slots__:
            raise AttributeError('Cannot set attribute on proxy.')
        return super(Proxy, self).__setattr__(attr, value) #type: ignore

        

    


