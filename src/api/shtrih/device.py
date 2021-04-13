import asyncio
import aioserial
import os
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from serial.tools import list_ports
from itertools import groupby
from src.api.device import Device, DeviceImpl, DeviceIOError, DeviceConnectionError
from src.api.shtrih.protocol import ShtrihProtoInterface
from binascii import hexlify


class SerialDevice(DeviceImpl):
    device = None 
    connected = False

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
        try:
            cls.device = aioserial.AioSerial(
                port=str(port), 
                baudrate=int(os.environ.get("PAYKIOSK_BAUDRATE")), #type: ignore
                dsrdtr=bool(int(os.environ.get("PAYKIOSK_FLOW_CONTROL","0"))), 
                rtscts=bool(int(os.environ.get("PAYKIOSK_FLOW_CONTROL","0"))),
                write_timeout=float(int(os.environ.get("PAYKIOSK_WRITE_TIMEOUT",5000))/1000), #type: ignore
                loop=asyncio.get_running_loop())
            try:
                cls.device.flushInput()
            except:
                pass
        except Exception as e:
            raise e 
        else:
            cls.connected = True

    @classmethod
    async def _read(cls, size):
        try:
            output = await cls.device.read_async(size)
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

class Paykiosk(Device, ShtrihProtoInterface):

    def __init__(self):
        Device.__init__(self)
        ShtrihProtoInterface.__init__(self)
        self.impl = None
        self.discover()

    @property
    def in_waiting(self):
        return self.impl.device.in_waiting

    def discover(self):
        if os.environ['PAYKIOSK_TYPE'] == 'SERIAL':
            self.impl = SerialDevice()
        elif os.environ['PAYKIOSK_TYPE'] != 'SERIAL':
            raise NotImplementedError
        return self.impl

    async def connect(self):
        await logger.info("Connecting to fiscalreg device...")
        while not self.impl.connected:
            try:
                await self.impl._open()
            except DeviceConnectionError as e:
                await logger.error(e)
                await asyncio.sleep(3)
                continue
            else:
                await logger.info("Connecton to fiscalreg device established")


    async def reconnect(self):
        self.impl.connected = False
        await self.connect()
            
    async def disconnect(self):
        await self.impl._close()

    async def read(self, size:int):
       while True:
            try:
                data = await self.impl._read(size)
                asyncio.ensure_future(logger.info(f'INPUT:{hexlify(bytes(data), sep=":")}'))
                return data
            except (DeviceConnectionError, DeviceIOError):
                await self.reconnect()
                continue
           

    async def write(self, data:bytearray):
        while True:
            try:
                await self.impl._write(data)
                asyncio.ensure_future(logger.info(f'OUTPUT:{hexlify(bytes(data), sep=":")}'))
                break
            except (DeviceConnectionError, DeviceIOError):
                await self.reconnect()
                continue
           

    async def poll(self):
        try:
            if self.in_waiting >0:
                await self.consume()
            else:
                await asyncio.sleep(0.1)
        except (OSError, DeviceConnectionError, DeviceIOError):
            await self.reconnect()
    
          
        

