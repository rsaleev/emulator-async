import os
import aioserial
import asyncio
from escpos.printer import Dummy
import usb
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from src import config
from binascii import hexlify
from typing import Deque, Union
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from src.db.models import States
from src.api.device import *
from src.api.printer.protocol import PrinterProto
from src.api.printer import logger


class UsbDevice(DeviceImpl):

    device = None
    connected = False

    READ_EXECUTOR = ThreadPoolExecutor(max_workers=1)
    WRITE_EXECUTOR = ThreadPoolExecutor(max_workers=1)

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
        if not cls.device:
            raise DeviceConnectionError("Device not found or cable not plugged in.")
        else:
            try:
                usb.util.dispose_resources(cls.device)
            except:
                raise DeviceConnectionError("Couldn't dispose resources")
            interface = 0
            if cls.device.is_kernel_driver_active(0):#type: ignore
                cls.device.detach_kernel_driver(0)#type: ignore
            if cls.device.is_kernel_driver_active(1):#type: ignore
                cls.device.detach_kernel_driver(1)#type: ignore
            while not cls.connected:
                try:
                    cfg = cls.device.get_active_configuration() #type: ignore
                    cls.device.set_configuration(cfg) #type: ignore
                    #type: ignore
                # ignore exception and proceed: reset device and get configuration again
                except usb.core.USBError as e:
                    print(e)
                    cls.device.reset() #type: ignore
                    time.sleep(1)
                    continue
                else:
                    # try to claim same interface 
                    try:
                        usb.util.release_interface(cls.device, interface)
                        usb.util.claim_interface(cls.device, interface)
                    except:
                        pass
                    break
            cls.endpoint_in = cls.device[0][(0,0)][0] #type: ignore
            cls.endpoint_out = cls.device[0][(0,0)][1] #type: ignore

    @classmethod
    def _close(cls):
        try:
            cls.WRITE_EXECUTOR.shutdown(wait=False)
            cls.READ_EXECUTOR.shutdown(wait=False)
        except:
            pass
        try:
            #clear app resources
            usb.util.dispose_resources(cls.device)
            cls.device.reset() #type: ignore
        except:
            pass

    @classmethod
    async def _connect(cls):
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                await loop.run_in_executor(executor, cls._open)
            except Exception as e:
                await asyncio.sleep(0.5)
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
            return await loop.run_in_executor(cls.READ_EXECUTOR, cls.device.read, cls.endpoint_in.bEndpointAddress, cls.endpoint_in.wMaxPacketSize, cls.read_timeout) #type: ignore
        except (usb.core.USBError, IOError) as e:
            raise DeviceIOError(e)
        except  usb.core.USBTimeoutError as e:
            raise DeviceTimeoutError(e)

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
            await loop.run_in_executor(cls.WRITE_EXECUTOR, cls.device.write, cls.endpoint_out.bEndpointAddress, data) #type:ignore
        except (usb.core.USBError, IOError) as e:
            raise DeviceIOError(e)
        except usb.core.USBTimeoutError as e:
            raise DeviceTimeoutError(e)

    

    @classmethod
    async def _reconnect(cls): 
        pass
    
    @classmethod
    async def _disconnect(cls):
        # graceful shutdown with clearance
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            await loop.run_in_executor(executor, cls._close)
        
            
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
    def _close(cls):
        try:
            cls.device.flushOutput()
            cls.device.flushInput()
            cls.device.flush()
            cls.device.close()
        except:
            pass

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
        pass
            
    @classmethod
    async def _disconnect(cls):        
        await cls.device._cancel_read_async()
        await cls.device._cancel_write_async()
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            await loop.run_in_executor(executor, cls._close)

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
                try:
                    await self._impl._connect()
                except DeviceConnectionError as e:
                    logger.debug(f'Connection error: {e}.Continue after 1 second')
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
                logger.info("Connecton aborted")          
        else:
            logger.error('Implementation not found')
            raise DeviceConnectionError('Implementation not found')

    async def disconnect(self):
        await self._impl._disconnect()

    async def reconnect(self):
        logger.warning('Reconnecting...')
        self._impl.connected = False
        while not self.event.is_set() and not self._impl.connected:
            try:
                await self.connect()
                logger.warning(f'Reconnected')
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(1)
                continue
            else:
                break
                
    async def read(self, size:int):
        # 5 attempts to read requested bytes
        attempts = 5
        # counter
        count = 1
        # while not send an event flag
        while not self.event.is_set():
            try:
                output = await self._impl._read(size)
            except (DeviceConnectionError, DeviceIOError) as e:
                logger.error(e)            
                await asyncio.create_task(self.reconnect())
                continue
            except DeviceTimeoutError as e:
                if count <= attempts:
                    logger.error(f'{e}. Counter={count}. Max attempts={attempts}')
                    await asyncio.sleep(0.5)
                    count+=1
                    continue
                else:
                    break
            else:
                logger.debug(f'INPUT: {hexlify(output, sep=":")}')
                return output

    async def write(self, data:Union[bytearray, bytes]):
        # 5 attempts to write bytes
        attempts = 5
        # counter
        count = 1
        while not self.event.is_set():
            try:
                await self._impl._write(data)
            except (DeviceConnectionError, DeviceIOError) as e:
                logger.error(e)
                await asyncio.create_task(self.reconnect())
                continue
            except DeviceTimeoutError as e:
                if count <= attempts:
                    logger.error(f'{e}. Counter={count}. Max attempts={attempts}')
                    await asyncio.sleep(0.5)
                    count+=1
                    continue
                else:
                    break
            else:
                logger.debug(f'OUTPUT: {hexlify(data, sep=":")}')
                break
                