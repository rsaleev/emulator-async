import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
import aioserial
import os
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from src.api.device import Device, DeviceImpl, DeviceIOError, DeviceConnectionError, DeviceTimeoutError
from src.api.shtrih.protocol import ShtrihProtoInterface
from binascii import hexlify


class SerialDevice(DeviceImpl):
    device = None 
    connected = False

    @classmethod
    async def _open(cls):
        cls.device = aioserial.AioSerial(
            port=os.environ.get("PAYKIOSK_PORT"), 
            baudrate=int(os.environ.get("PAYKIOSK_BAUDRATE")), #type: ignore
            dsrdtr=bool(int(os.environ.get("PAYKIOSK_FLOW_CONTROL","0"))), 
            rtscts=bool(int(os.environ.get("PAYKIOSK_FLOW_CONTROL","0"))),
            timeout=float(int(os.environ.get("PAYKIOSK_READ_TIMEOUT",5000))/1000), #type_ignore
            write_timeout=float(int(os.environ.get("PAYKIOSK_WRITE_TIMEOUT",5000))/1000),
            cancel_read_timeout=round(int(os.environ.get("PAYKIOSK_READ_TIMEOUT",5000))//1000,1),
            cancel_write_timeout=round(int(os.environ.get("PAYKIOSK_WRITE_TIMEOUT",5000))//1000,1))
     
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
            cls.device.flushInput()
            cls.device.flushOutput()
        except Exception as e:
            raise e

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
    async def _disconnect(cls):
        await cls.device._cancel_read_async()
        await cls.device._cancel_write_async()
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            await loop.run_in_executor(executor, cls._close)

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

    async def connect(self):
        logger.info("Connecting to fiscalreg device...")
        if self._impl:
            while not self.event.is_set():
                try:
                    await self._impl._connect()
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
        else:
            logger.error('Implementation not found')
            raise DeviceConnectionError('Paykiosk device implementation not found')

    async def disconnect(self):
        await self._impl._disconnect()

    async def reconnect(self):
        await logger.warning('Reconnecting to device')
        while not self.event.is_set():
            try:
                await self.connect()
            except:
                await asyncio.sleep(0.5)
                continue
            else:
                await logger.warning('Reconnected successfully')
                break
        
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
                logger.debug(f'OUTPUT BUFFER: {self._impl.device.in_waiting}')
                break

    async def poll(self):
        while not self.event.is_set():
            try:
                if self._impl.device.in_waiting >0:
                    await self.consume()
                else:
                    await asyncio.sleep(0.02)
            except (OSError, DeviceConnectionError, DeviceIOError) as e:
                await logger.error(e)
                await self.reconnect()
                if self._impl.connected:
                    continue
    
          
        

