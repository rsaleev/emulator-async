import os
import aioserial
import asyncio
import usb
from concurrent.futures import ThreadPoolExecutor
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
            try:
                for config in cls.device:
                    try:
                        for i in range(config.bNumInterfaces): #type: ignore
                            cls.device.detach_kernel_driver(i) #type: ignore
                    except Exception as e:
                        pass  #type: ignore
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
            output = await loop.run_in_executor(cls.EXECUTOR, cls.device.read, cls.IN_EP, size, cls.READ_TIMEOUT) #type: ignore
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
            await loop.run_in_executor(cls.EXECUTOR, cls.device.write, cls.OUT_EP, data, cls.WRITE_TIMEOUT) #type:ignore
        except (usb.core.USBError, usb.core.USBTimeoutError, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    def _close(cls):
        try:
            cls.EXECUTOR.shutdown(wait=True)
            usb.util.dispose_resources(cls.device)
        except:
            pass

    @classmethod
    async def _reconnect(cls):
        cls.connected = False
        while not cls.connected:
            await cls._open()
class SerialDevice(DeviceImpl):
    device = None 
    connected = False

    @classmethod
    async def _open(cls):
        try:
            cls.device = aioserial.AioSerial(
                port=os.environ.get("PRINTER_PORT"), 
                baudrate=int(os.environ.get("PRINTER_BAUDRATE")), #type: ignore
                dsrdtr=bool(int(os.environ.get("PRINTER_FLOW_CONTROL"))), #type: ignore
                rtscts=bool(int(os.environ.get("PRINTER_FLOW_CONTROL"))), #type: ignore
                write_timeout=float(int(os.environ.get("PRINTER_WRITE_TIMEOUT"))/1000), #type: ignore
                timeout=float(int(os.environ.get("PRINTER_READ_TIMEOUT"))/1000), #type: ignore
                loop=asyncio.get_running_loop())
            cls.device.flushOutput()
            cls.device.flushInput()
        except Exception as e:
            logger.exception(e)
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
        if os.environ.get('PRINTER_TYPE') == 'USB':
            self._impl = UsbDevice()
        elif os.environ.get('PRINTER_TYPE') == 'SERIAL':
            self._impl = SerialDevice()

    async def connect(self):
        await States.filter(id=1).update(submode=1)
        logger.info(f'Connecting to printer device...')
        if self._impl:
            while not self._impl.connected:
                try:
                    await self._impl._open()
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
        while not self._impl.connected:
            await self._impl._reconnect()

    def disconnect(self):
        self._impl._close()

    async def read(self, size:int):
        # 5 attempts to read requested bytes
        attempts = 5
        # basic output if no data can be read
        output = b''
        # counter
        count = 0
        # while not send an event flag
        while not self.event.is_set():
            try:
                while len(output)<size and count<= attempts:
                    try:
                        output = await self._impl._read(6)
                    except:
                        count+=1
                        continue
                    else:
                        break
                else:
                    raise DeviceIOError(f'{count} attempts were used to read data from port')
            except (DeviceConnectionError, DeviceIOError) as e:
                logger.exception(e)
                raise e
                # fut = asyncio.ensure_future(self.reconnect())
                # while not fut.done():
                #     await asyncio.sleep(0.5)
                # else:
                #     if not fut.exception():
                #         break
            else:
                asyncio.ensure_future(logger.debug(f'INPUT: {hexlify(output, sep=":")}'))
                return output

    async def write(self, data:Union[bytearray, bytes]):
        while not self.event.is_set():
            try:
                await self._impl._write(data)
            except (DeviceConnectionError, DeviceIOError) as e:
                asyncio.ensure_future(logger.exception(e))
                fut = asyncio.ensure_future(self.reconnect())
                while not fut.done():
                    await asyncio.sleep(0.5)
                else:
                    if not fut.exception():
                        break
            else:
                asyncio.ensure_future(logger.debug(f'OUTPUT: {hexlify(data, sep=":")}'))
                break
                
               