from src.api.device import AbstractDevice
from src.api.shtrih.protocol import ShtrihProto
import asyncio
import aioserial
import os
import asyncio



class ShtrihProxyDevice(AbstractDevice):
    pass

class ShtrihDevice(AbstractDevice, ShtrihProto):

    def __init__(self):
    
        self.device = None
        self.buffer = asyncio.Queue()

class ShtrihSerialDevice(ShtrihDevice):

    def __init__(self):
        super().__init__()
        self.port = os.environ.get("SHTRIH_SERIAL_PORT", "/dev/ttyUSB0")
        self.baudrate = int(os.environ.get("SHTRIH_SERIAL_BAUDRATE", "115200"))
        self.timeout = int(os.environ.get("SHTRIH_SERIAL_TIMEOUT", "2"))

    async def discover(self):
        pass

    async def connect(self):
        self.device = aioserial.AioSerial(port=self.port, baudrate=self.baudrate, write_timeout=self.timeout, loop=asyncio.get_running_loop())
        return self.device

    async def reconnect(self):
        if not self.device.isOpen():
            await self.connect()
        else:
            self.device.cancel_read()
            self.device.cancel_write()
            self.device.flush()
            
    async def disconnect(self):
        pass

    async def write(self, data:bytearray) ->None:
        await self.device.write_async(data)

    async def read(self, size:int) -> bytearray:
        return bytearray(await self.device.read_async(size))

    
        

