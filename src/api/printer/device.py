import os
import aioserial
import asyncio
from src import config
from binascii import hexlify
from typing import Union
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from src.db.models import States
from src.api.device import *
from escpos.printer import Dummy
from src.api.printer.protocol import PrinterProto
from src.api.printer import logger


class SerialDevice(DeviceImpl):
    device = None 

    @classmethod
    async def _open(cls):
        cls.device = aioserial.AioSerial(
            port=os.environ.get("PRINTER_PORT"), 
            baudrate=int(os.environ.get("PRINTER_BAUDRATE")), #type: ignore
            dsrdtr=bool(int(os.environ.get("PRINTER_FLOW_CONTROL","1"))), 
            rtscts=bool(int(os.environ.get("PPRINTER_FLOW_CONTROL","1"))),
            write_timeout=float(int(os.environ.get("PRINTER_WRITE_TIMEOUT",5000))/1000), #type: ignore
            timeout=float(int(os.environ.get("PRINTER_READ_TIMEOUT",5000))/1000),
            loop=asyncio.get_running_loop())
        try:
            cls.device.flushInput()
        except Exception as e:
            raise e 
        else:
            return True

    @classmethod
    async def _read(cls, size):
        try:
            output = await cls.device.read_async(size)
        except (SerialException, SerialTimeoutException, IOError) as e:
            raise DeviceIOError(e)
        else:
            return output


    @classmethod
    async def _write(cls, data):
        try:
            await cls.device.write_async(data)
        except (SerialException, SerialTimeoutException, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    async def _reconnect(cls):
        cls.connected = False
        while not cls.connected:
            await cls._open()

    @classmethod
    def _close(cls):
        try:
            cls.device.cancel_read()
            cls.device.cancel_write()
            cls.device.close()
        except:
            pass

class Printer(PrinterProto, Device):

    buffer = Dummy()
    event:asyncio.Event

    def __init__(self):
        PrinterProto.__init__(self)
        self._impl = None
        self.discover()
        self.event = asyncio.Event()
        self.connected = False
        

    def discover(self):
       self._impl = SerialDevice()

    async def connect(self):
        await States.filter(id=1).update(submode=1)
        logger.info(f'Connecting to printer device...')
        if self._impl:
            while not self.connected:
                try:
                    self.connected = await self._impl._open()
                    logger.info('Connection to printer established')
                    self.profile.profile_data['media']['width']['pixels'] = int(
                        os.environ.get("PRINTER_PAPER_WIDTH", 540))  #type:ignore
                    if config['printer']['presenter']['continuous']:
                        await self.write(bytearray((0x1D, 0x65, 0x14)))
                    await States.filter(id=1).update(submode=0)
                    return self.connected
                except DeviceConnectionError as e:
                    logger.error(e)
                    await asyncio.sleep(1)
                    continue                   
        else:
            logger.error('Implementation not found')

    async def reconnect(self):
        await States.filter(id=1).update(submode=1)
        await asyncio.sleep(1)
        while not self.connected:
            await self._impl._reconnect()

    def disconnect(self):
        self._impl._close()

    async def read(self, size:int):
        while not self.event.is_set():
            try:
                output = await self._impl._read(6)
                logger.debug(f'INPUT: {hexlify(output, sep=":")}')
            except (DeviceConnectionError, DeviceIOError) as e:
                logger.exception(e)
                fut = asyncio.ensure_future(self.reconnect())
                if fut.done():
                    continue
            else:
                return output

    async def write(self, data:Union[bytearray, bytes]):
        while not self.event.is_set():
            try:
                logger.debug(f'OUTPUT: {hexlify(data, sep=":")}')
                await self._impl._write(data)
                await asyncio.sleep(0.5)
                break
            except (DeviceConnectionError, DeviceIOError) as e:
                asyncio.ensure_future(logger.exception(e))
                fut = asyncio.ensure_future(self.reconnect())
                if fut.done():
                    continue
