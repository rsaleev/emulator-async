import os
import usb
import aioserial
import asyncio
from binascii import hexlify
from concurrent.futures import ThreadPoolExecutor
from itertools import groupby
from functools import partial
from typing import Union
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from src.db.models import States
from serial.tools import list_ports
from src import config
from src.api.device import *
from escpos.printer import Dummy
from src.api.printer.protocol import PrinterProto
from src.api.printer import logger

class UsbDevice(DeviceImpl):

    device = None
    connected = False

    EXECUTOR = ThreadPoolExecutor(max_workers=1)

    VENDOR_ID = int(os.environ.get('PRINTER_VENDOR_ID'),16) #type: ignore
    PRODUCT_ID =int(os.environ.get('PRINTER_PRODUCT_ID'),16) #type: ignore
    IN_EP = int(os.environ.get('PRINTER_IN_EP'),16) #type: ignore
    OUT_EP = int(os.environ.get('PRINTER_OUT_EP'),16) #type: ignore
    WRITE_TIMEOUT = int(os.environ.get('PRINTER_WRITE_TIMEOUT')) #type: ignore
    READ_TIMEOUT = int(os.environ.get('PRINTER_READ_TIMEOUT')) #type: ignore


    @classmethod
    async def _open(cls):
        """_open 
        

        [extended_summary]

        Raises:
            DeviceConnectionError: includes USB errors and OS errors if device not accessable
            
        """
        cls.device = usb.core.find(
            idVendor= cls.VENDOR_ID,
            idProduct=cls.PRODUCT_ID)
        
        if cls.device is None:
            raise DeviceConnectionError(
                "Device not found or cable not plugged in.")
        if cls.device.backend.__module__.endswith("libusb1"):  #type: ignore
            check_driver = None
            try:
                check_driver = cls.device.is_kernel_driver_active(0)  #type: ignore
            except NotImplementedError:
                pass
            if check_driver is None or check_driver:
                try:
                    cls.device.detach_kernel_driver(0)  #type: ignore
                except NotImplementedError:
                    pass
                except usb.core.USBError as e:
                    if check_driver is not None:
                        raise DeviceConnectionError(
                            "Could not detatch kernel driver: {0}".format(
                                str(e)))
        try:
            cls.device.set_configuration()  #type: ignore
            cls.device.reset()  #type: ignore
        except usb.core.USBError as e:
            raise DeviceConnectionError(
                "Could not set configuration: {0}".format(str(e)))
        else:
            cls.connected = True

    
    @classmethod
    async def _read(cls, size):
        """ 
        asynchronous implementation for dev.read()

        usage: run in executor to prevent blocking looop

        Raises:
            DeviceIOError: incapsulates exceptions: USBError, USBTimeoutError, IOError
        """
        loop = asyncio.get_running_loop()
        try:
            output = await loop.run_in_executor(None, partial(cls.device.read, cls.IN_EP, 16, cls.READ_TIMEOUT)) #type: ignore
        except (usb.core.USBError, usb.core.USBTimeoutError, IOError) as e:
            raise DeviceIOError(e)
        else:
            asyncio.ensure_future(logger.debug(f'INPUT: {output}'))
            return output

    @classmethod
    async def _write(cls, data:bytes):
        """ 
        asynchronous implementation for dev.read()

        usage: run in executor to prevent blocking looop

        Raises:
            DeviceIOError: incapsulates exceptions: USBError, USBTimeoutError, IOError
        """
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, partial(cls.device.write, cls.OUT_EP, data, cls.WRITE_TIMEOUT)) #type:ignore
        except (usb.core.USBError, usb.core.USBTimeoutError, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    async def _close(cls):
        loop = asyncio.get_running_loop()
        try:
            asyncio.wait_for(loop.run_in_executor(None, partial(usb.util.dispose_resources, cls.device)),0.5)
        except:
            pass

class SerialDevice(DeviceImpl):
    device = None 
    connected = False

    @classmethod
    async def _open(cls):
        port = os.environ.get("PRINTER_SERIAL_PORT", "/dev/ttyUSB0")
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
                baudrate=int(os.environ.get("PRINTER_BAUDRATE")), #type: ignore
                dsrdtr=bool(int(os.environ.get("PRINTER_FLOW_CONTROL","0"))), 
                rtscts=bool(int(os.environ.get("PPRINTER_FLOW_CONTROL","0"))),
                write_timeout=float(int(os.environ.get("PRINTER_WRITE_TIMEOUT",1000))/1000), #type: ignore
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
    async def _close(cls):
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
        

    def discover(self):
        if os.environ['PRINTER_TYPE'] == 'USB':
            self._impl = UsbDevice()
        elif os.environ['PRINTER_TYPE'] == 'SERIAL':
            self._impl = SerialDevice()
        return self._impl

    async def connect(self):
        await States.filter(id=1).update(submode=1)
        await  logger.info(f'Connecting to printer device...')
        if self._impl:
            while not self._impl.connected:
                try:
                    await self._impl._open()
                except DeviceConnectionError as e:
                    asyncio.ensure_future(logger.error(e))
                    await asyncio.sleep(1)
                    continue
                else:
                    await logger.info('Connection to printer established')
                    self.profile.profile_data['media']['width']['pixels'] = int(
                        os.environ.get("PRINTER_PAPER_WIDTH", 540))  #type:ignore
                    if config['printer']['presenter']['continuous']:
                        await self.write(bytearray((0x1D, 0x65, 0x14)))
                    await States.filter(id=1).update(submode=0)
                    return self.device
        else:
            asyncio.ensure_future(logger.error('Implementation not found'))

    async def reconnect(self):
        await States.filter(id=1).update(submode=1)
        await asyncio.sleep(1)
        if self._impl:
            await asyncio.sleep(1)
            self._impl.connected = False
            await self.connect()

    async def disconnect(self):
        self.hw('INIT')
        await self._impl._close()

    async def read(self, size:int):
        while not self.event.is_set():
            try:
                output = await self._impl._read(size)
                asyncio.ensure_future(logger.debug(f'INPUT: {hexlify(output, sep=":")}'))
            except (DeviceConnectionError, DeviceIOError) as e:
                asyncio.ensure_future(logger.exception(e))
                fut = asyncio.ensure_future(self.reconnect())
                if fut.done():
                    continue
            else:
                return output

    async def write(self, data:Union[bytearray, bytes]):
        while 1:
            try:
                await self._impl._write(bytes(data))
                asyncio.ensure_future(logger.debug(f'OUTPUT: {hexlify(data, sep=":")}'))
            except (DeviceConnectionError, DeviceIOError) as e:
                asyncio.ensure_future(logger.exception(e))
                fut = asyncio.ensure_future(self.reconnect())
                if fut.done():
                    continue
            else:
                break
