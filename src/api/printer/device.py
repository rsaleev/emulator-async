
from src.api.printer.protocol import PrinterProto
from src.api.device import AbstractDevice
from escpos.printer import Dummy
import asyncio 
from functools import partial
from src.api.printer.commands import COMMANDS



class PrinterDevice(AbstractDevice, PrinterProto):
    def __init__(self):
        AbstractDevice.__init__(self)
        PrinterProto.__init__(self)
        self.device = None
        self.buffered = False
        self.buffer = Dummy()
        self.loop = asyncio.get_event_loop()

    async def write(self, data):
        """write [summary]

        [extended_summary]

        Args:
            data ([type]): [description]
        """
        if self.buffered:
            self.buffer._raw(data)
            return None
        else:
            self.loop.create_task(cls.loop.run_in_executor(None, partial(self.device.write, data))) # type: ignore
        

    async def read(self, size:int):
        """read [summary]

        [extended_summary]

        Args:
            size (int): [description]
        """
        self.loop.create_task(cls.loop.run_in_executor(None, partial(cls.device.read, size))) # type: ignore

    async def _raw(self, data):
        return self.write(data)

class PrinterProxyDevice(PrinterDevice, PrinterProto):
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
            return getattr(self.obj, method)(*args, **kwargs)
        return inner

    def __getattr__(self, attr):
        if self.obj is None:
            raise AttributeError('Cannot use uninitialized Proxy.')
        return getattr(self.obj, attr)

    def __setattr__(self, attr, value):
        if attr not in self.__slots__:
            raise AttributeError('Cannot set attribute on proxy.')
        return super(PrinterProxyDevice, self).__setattr__(attr, value)

    def write(self, data):
        return super().write(data)

    def read(self, size: int):
        return super().read(size)

class PrinterUsbDevice(PrinterDevice, PrinterProto):

    @classmethod
    async def discover(cls):
        pass


    @classmethod
    async def _raw(cls, data):
        pass
