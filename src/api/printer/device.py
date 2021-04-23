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

    READ_EXECUTOR = ThreadPoolExecutor(max_workers=1)
    READ_LOCK = asyncio.Lock()
    WRITE_EXECUTOR = ThreadPoolExecutor(max_workers=1)
    WRITE_LOCK = asyncio.Lock()

    vendor_id = int(os.environ.get('PRINTER_VENDOR_ID'),16) #type: ignore
    product_id =int(os.environ.get('PRINTER_PRODUCT_ID'),16) #type: ignore
    write_timeout = int(os.environ.get('PRINTER_WRITE_TIMEOUT')) #type: ignore
    read_timeout = int(os.environ.get('PRINTER_READ_TIMEOUT')) #type: ignore
    endpoint_in = None 
    endpoint_out = None


    @classmethod
    def _open(cls):
        """_open 
        [extended_summary]

        Raises:
            DeviceConnectionError: includes USB errors and OS errors if device not accessable
            
        """
        cls.device = usb.core.find(
            idVendor= cls.vendor_id,
            idProduct=cls.product_id)
        if cls.device is None:
            raise DeviceConnectionError("Device not found or cable not plugged in.")
        try:
            usb.util.dispose_resources(cls.device)
        except:
            raise DeviceConnectionError("Couldn't dispose resources")
        interface = 0
        if cls.device.is_kernel_driver_active(0):#type: ignore
            cls.device.detach_kernel_driver(0)#type: ignore
        if cls.device.is_kernel_driver_active(1):#type: ignore
            cls.device.detach_kernel_driver(1)#type: ignore
        try:
            cls.device.set_configuration() #type: ignore
            #type: ignore
        except usb.core.USBError as e:
            raise DeviceConnectionError(f"Could not set configuration: {e}")
        try:
            usb.util.claim_interface(cls.device, interface)
        except:
            logger.warning(DeviceConnectionError("Couldn't claim interface. Continue"))
        cls.endpoint_in = cls.device[0][(0,0)][0] #type: ignore
        cls.endpoint_out = cls.device[0][(0,0)][1] #type: ignore

    @classmethod
    async def _connect(cls):
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                await loop.run_in_executor(executor, cls._open)
            except Exception as e:
                raise e
            else:
                cls.connected = True
    @classmethod
    async def _read(cls, size=None): 
        """ 
        asynchronous implementation for dev.read()

        usage: run in executor to prevent blocking looop

        size = None: overrided with wMaxPacketSize value of endpoint

        Raises:
            DeviceIOError: incapsulates exceptions: USBError, IOError
            DeviceTimeoutError:  USBTimeoutError
        """
        loop = asyncio.get_running_loop()
        try:
            async with cls.READ_LOCK:
                output = await loop.run_in_executor(cls.READ_EXECUTOR, cls.device.read, cls.endpoint_in.bEndpointAddress, cls.endpoint_in.wMaxPacketSize, cls.read_timeout) #type: ignore
        except (usb.core.USBError, IOError) as e:
            raise DeviceIOError(e)
        except  usb.core.USBTimeoutError as e:
            raise DeviceTimeoutError(e)
        else:
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
            async with cls.WRITE_LOCK:
                await loop.run_in_executor(cls.WRITE_EXECUTOR, cls.device.write, cls.endpoint_out.bEndpointAddress, data) #type:ignore
        except (usb.core.USBError, IOError) as e:
            raise DeviceIOError(e)
        except usb.core.USBTimeoutError as e:
            raise DeviceTimeoutError(e)

    @classmethod
    def _close(cls):
       pass

    @classmethod
    async def _reconnect(cls):
        usb.util.dispose_resources(cls.device)
        await cls._connect()

    @classmethod
    async def _disconnect(cls):
         # graceful shutdown with clearance
        try:
            cls.WRITE_EXECUTOR.shutdown(wait=True)
            cls.READ_EXECUTOR.shutdown(wait=True)
        except:
            pass
        try:
            #clear app resources
            usb.util.dispose_resources(cls.device)
            cls.device.reset() #type: ignore
        except:
            pass
            
class SerialDevice(DeviceImpl):

    device = None 
    connected = False

    @classmethod
    async def _open(cls):
        cls.device = aioserial.AioSerial(
            port=os.environ.get("PRINTER_PORT"), 
            baudrate=int(os.environ.get("PRINTER_BAUDRATE")), #type: ignore
            dsrdtr=bool(int(os.environ.get("PRINTER_FLOW_CONTROL"))), #type: ignore
            rtscts=bool(int(os.environ.get("PRINTER_FLOW_CONTROL"))), #type: ignore
            write_timeout=float(int(os.environ.get("PRINTER_write_timeout"))/1000), #type: ignore
            timeout=float(int(os.environ.get("PRINTER_read_timeout"))/1000)) #type: ignore

    @classmethod
    async def _connect(cls):
        try:
            await cls._open()
        except Exception as e:
            raise e
        else:
            cls.device.flushOutput()
            cls.device.flushInput()
            cls.connected = True

    @classmethod
    async def _read(cls, size):
        try:
            return await cls.device.read_async(size)
        except (SerialException, IOError) as e:
            raise DeviceIOError(e)
        except SerialTimeoutException as e:
            raise DeviceTimeoutError(e)
       

    @classmethod
    async def _write(cls, data):
        try:
            await cls.device.write_async(data)
        except (SerialException, IOError) as e:
            raise DeviceIOError(e)
        except  SerialTimeoutException as e:
            raise DeviceTimeoutError(e)

    @classmethod
    async def _reconnect(cls):
        cls.device.cancel_read()
        cls.device.cancel_write()
        cls.device.flushInput()
        cls.device.flushOutput()
        await cls._connect()

    @classmethod
    async def _disconnect(cls):
        try:
            cls.device.cancel_read()
            cls.device.cancel_write()
            cls.device.flushOutput()
            cls.device.flushInput()
            cls.device.flush()
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
        if os.environ.get('PRINTER_TYPE') == 'USB':
            self._impl = UsbDevice()
        elif os.environ.get('PRINTER_TYPE') == 'SERIAL':
            self._impl = SerialDevice()

    async def connect(self):
        await States.filter(id=1).update(submode=1)
        logger.info(f'Connecting to printer device...')
        if self._impl:
            while not self.event.is_set():
                if not self._impl.connected:
                    try:
                        await self._impl._connect()
                    except DeviceConnectionError as e:
                        logger.error(f'Connection error: {e}.Continue after 1 second')
                        await asyncio.sleep(1)
                        continue 
                    else:
                        logger.info('Connection to printer established')
                        self.profile.profile_data['media']['width']['pixels'] = int(
                            os.environ.get("PRINTER_PAPER_WIDTH", 540))  #type:ignore
                        if config['printer']['presenter']['continuous']:
                            await self.write(bytearray((0x1D, 0x65, 0x14)))
                        await States.filter(id=1).update(submode=0)
                        return self._impl 
                else:
                    break
            else:
                logger.info("Connecton aborted")          
        else:
            logger.error('Implementation not found')
            raise DeviceConnectionError('Implementation not found')

    async def disconnect(self):
        await self._impl._disconnect()

    async def reconnect(self):
        await States.filter(id=1).update(submode=1)
        while not self.event.is_set():
            await self._impl._reconnect()
            if self._impl.connected:
                break
            else:
                await asyncio.sleep(0.5)
                continue

    async def read(self, size:int):
        # 5 attempts to read requested bytes
        attempts = 5
        # counter
        count = 0
        # while not send an event flag
        while not self.event.is_set():
            try:
                output = await self._impl._read(size)
            except (DeviceConnectionError, DeviceIOError) as e:
                self._impl.connected = False
                logger.error(f'{e}. Reconnecting')            
                fut = asyncio.ensure_future(self.reconnect())
                while not fut.done():
                    await asyncio.sleep(0.5)
                else:
                    if not fut.exception():
                        continue
            except DeviceTimeoutError as e:
                if count <= attempts:
                    logger.error(f'{e}. Counter={count}. Max attempts={attempts}')
                    await asyncio.sleep(0.5)
                    count+=1
                    continue          
            else:
                logger.debug(f'INPUT: {hexlify(output, sep=":")}')
                return output

    async def write(self, data:Union[bytearray, bytes]):
        # 5 attempts to write bytes
        attempts = 5
        # counter
        count = 0
        while not self.event.is_set():
            try:
                await self._impl._write(data)
            except (DeviceConnectionError, DeviceIOError) as e:
                self._impl.connected = False
                logger.error(e)
                fut = asyncio.ensure_future(self.reconnect())
                while not fut.done():
                    await asyncio.sleep(0.5)
                else:
                    if not fut.exception():
                        continue
            except DeviceTimeoutError as e:
                if count <= attempts:
                    logger.error(f'{e}. Counter={count}. Max attempts={attempts}')
                    await asyncio.sleep(0.5)
                    count+=1
                    continue  
            else:
                logger.debug(f'OUTPUT: {hexlify(data, sep=":")}')
                break
                
               