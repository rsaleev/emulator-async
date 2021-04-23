import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Coroutine
import aioserial
import os
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from serial.tools import list_ports
from itertools import groupby
from src.api.device import Device, DeviceImpl, DeviceIOError, DeviceConnectionError, DeviceTimeoutError
from src.api.shtrih.protocol import ShtrihProtoInterface
from binascii import hexlify


class SerialDevice(DeviceImpl):
    device = None 
    connected = False

    @classmethod
    async def _open(cls):
        try:
            cls.device = aioserial.AioSerial(
                port=os.environ.get("PAYKIOSK_PORT"), 
                baudrate=int(os.environ.get("PAYKIOSK_BAUDRATE")), #type: ignore
                dsrdtr=bool(int(os.environ.get("PAYKIOSK_FLOW_CONTROL","0"))), 
                rtscts=bool(int(os.environ.get("PAYKIOSK_FLOW_CONTROL","0"))),
                timeout=float(int(os.environ.get("PAYKIOSK_READ_TIMEOUT",5000))/1000), #type_ignore
                write_timeout=float(int(os.environ.get("PAYKIOSK_WRITE_TIMEOUT",5000))/1000))
        except Exception as e:
            raise e 
        else:
            cls.connected = True

    @classmethod
    async def _read(cls, size):
        try:
            output = await cls.device.read_async(size)
        except (SerialException, IOError) as e:
            raise DeviceIOError(e)
        except SerialTimeoutException as e:
            raise DeviceTimeoutError(e)
        else:
            return output

    @classmethod
    async def _write(cls, data):
        try:
            await cls.device.write_async(data)
        except (SerialException, IOError) as e:
            raise DeviceIOError(e)
        except SerialTimeoutException as e:
            raise DeviceTimeoutError(e)

    @classmethod
    async def _reconnect(cls):
        try:
            cls.device.cancel_write()
            cls.device.cancel_write()
        except:
            pass
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            await loop.run_in_executor(executor, cls._open)


    @classmethod
    def _close(cls):
        try:
            cls.device.cancel_write()
            cls.device.cancel_write()
            cls.device.close()
        except:
            pass

class Paykiosk(Device, ShtrihProtoInterface):

    def __init__(self):
        Device.__init__(self)
        ShtrihProtoInterface.__init__(self)
        self._impl = None
        self.discover()
        self.event = asyncio.Event()

    def discover(self):
        if os.environ['PAYKIOSK_TYPE'] == 'SERIAL':
            self._impl = SerialDevice()
        elif os.environ['PAYKIOSK_TYPE'] != 'SERIAL':
            raise NotImplementedError
        return self._impl

    async def connect(self):
        logger.info("Connecting to fiscalreg device...")
        loop = asyncio.get_running_loop()
        if self._impl:
            while not self._impl.connected:
                if not self.event.is_set():
                    try:
                        if isinstance(self._impl._open, asyncio.Future):
                            await self._impl._open()
                        else:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                await loop.run_in_executor(executor, self._impl._open)
                    except (asyncio.TimeoutError,DeviceConnectionError) as e:
                        logger.error(f'Connection error: {e}.Continue after 1 second')
                        await asyncio.sleep(1)
                        continue
                    else:
                        try:
                            self._impl.device.flushInput()
                            self._impl.device.flushOutput()
                        except:
                            pass
                        logger.info("Connecton to fiscalreg device established")
                        break
                else:
                    logger.info("Connecton aborted")
                    break
        else:
            logger.error('Implementation not found')
            raise DeviceConnectionError('Implementation not found')


            
    async def disconnect(self):
        self._impl._close()

    async def reconnect(self):
        await self._impl._reconnect()
        

    async def read(self, size:int):
        attempts = 5
        count =0
        while not self.event.is_set() and count <=attempts:
            try:
                data = await self._impl._read(size)
            except (DeviceConnectionError, DeviceIOError) as e:
                logger.error(f'{e}. Reconnecting')            
                self._impl.connected = False
                await self.reconnect()
                continue
            except DeviceTimeoutError as e:
                logger.error(f'{e}. Counter={count}. Max attempts={attempts}')
                await asyncio.sleep(0.5)
                count +=1
                continue
            else:
                logger.info(f'INPUT:{hexlify(bytes(data), sep=":")}')
                return data

    async def write(self, data:bytearray):
        attempts = 5
        count =0
        while not self.event.is_set() and count <=attempts:
            try:
                await self._impl._write(data)
            except (DeviceConnectionError, DeviceIOError) as e:
                logger.error(f'{e}. Reconnecting')            
                self._impl.connected = False
                await self.reconnect()
                continue
            except DeviceTimeoutError as e:
                logger.error(f'{e}. Counter={count}. Max attempts={attempts}')
                await asyncio.sleep(0.2)
                count+=1
                continue
            else:
                logger.info(f'OUTPUT:{hexlify(bytes(data), sep=":")}')
                break

    async def poll(self):
        while not self.event.is_set():
            try:
                if self._impl.device.in_waiting >0:
                    await self.consume()
                else:
                    await asyncio.sleep(0.1)
            except (OSError, DeviceConnectionError, DeviceIOError):
                await self.reconnect()
                continue
    
          
        

