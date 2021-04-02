import asyncio
import aioserial
import os
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from serial.tools import list_ports
from itertools import groupby
from src.api.device import *
from src.api.shtrih.protocol import ShtrihProto
from binascii import hexlify


class SerialDevice(DeviceImpl):
    device = None 

    @classmethod
    async def _open(cls):
        port = os.environ.get("SHTRIH_SERIAL_PORT", "/dev/ttyUSB0")
        ports = list(list_ports.comports())
        if len(ports) > 1:
            hwids = [str(p[2]).split(" ") for p in ports] 
            counter, group = [(len(list(group)), key)
                              for key, group in groupby(hwids)][0]
            if counter > 1:
               await logger.error(f"Found multiple devices {counter} with same group {group}")
            else:
                port = ports[0][0]
        elif len(ports) == 0:
            await logger.error(f"Device not found with autodiscover connecting with default params")
        elif len(ports) == 1:
            port = ports[0][0]
        cls.device = aioserial.AioSerial(port=str(port), 
            baudrate=int(os.environ.get("SHTRIH_SERIAL_BAUDRATE", "115200")), 
            write_timeout=int(os.environ.get("SHTRIH_SERIAL_TIMEOUT", "2")), 
            loop=asyncio.get_running_loop())

    @classmethod
    async def _read(cls, size):
        try:
            output = cls.device.read_async(size)
            return output
        except (SerialException, SerialTimeoutException, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    async def _write(cls, data):
        try:
            await cls.device.write_async(data)
        except (SerialException, SerialTimeoutException, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    async def _close(cls):
        try:
            cls.device.cancel_read()
            cls.device.cancel_write()
            cls.device.close()
        except:
            pass

class Paykiosk(Device, ShtrihProto):

    def __init__(self):
        Device.__init__(self)
        ShtrihProto.__init__(self)
        self.impl = None
        self.device = None

    def discover(self):
        if os.environ['PAYKIOSK_TYPE'] == 'SERIAL':
            self.impl = SerialDevice()
        elif os.environ['PAYKIOSK_TYPE'] != 'SERIAL':
            raise NotImplementedError

    async def connect(self):
        await logger.info("Connecting to fiscalreg device...")
        while not self.device:
            try:
                self.device = await self.impl._open()
            except DeviceConnectionError as e:
                await logger.error(e)
                await asyncio.sleep(3)
                continue
            else:
                await logger.info("Connecton to fiscalreg device established")
                return self.device

    async def reconnect(self):
        self.device = None
        await self.connect()
            
    async def disconnect(self):
        await self.impl._close()

    async def read(self, size:int):
       while True:
            try:
                data = await self.impl._read(size)
                await logger.info(f'INPUT:{hexlify(bytes(data), sep=":")}') 
                return data
            except (DeviceConnectionError, DeviceIOError):
                await self.reconnect()
                continue

    async def write(self, data:bytearray):
        while True:
            try:
                task_write = self.impl._write(data)
                task_log = logger.info(f'OUTPUT:{hexlify(bytes(data), sep=":")}')
                await asyncio.gather(task_log, task_write)
                break
            except (DeviceConnectionError, DeviceIOError):
                await self.reconnect()
                continue

    async def serve(self):
        if self.impl.device.in_waiting:
            await self.consume()
        else:
            await asyncio.sleep(0.1)
    
        

