from src.api.shtrih.protocol import ShtrihProto
import asyncio
import aioserial
import os
import asyncio
from src.api.shtrih import logger

class ShtrihDevice(ShtrihProto):

    def __init__(self):
        self.device = None
        self.buffer = asyncio.Queue()

class ShtrihProxyDevice(ShtrihProto):
    device = None
    buffer = None
    
    @classmethod
    def init_proxy(cls, device:object, buffer:object):
        cls.device = device
        cls.buffer = buffer

    @classmethod
    async def send(cls, arr:bytearray) -> None:
        crc = cls.crc_calc(arr)
        arr.extend(crc)
        output = bytearray()
        output.extend(cls.STX)
        output.extend(arr)
        await cls.buffer.put(output) #type: ignore
        await cls.device.write(output) #type: ignore
        await logger.debug(f'OUTPUT:{output}')
    
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

    
        

