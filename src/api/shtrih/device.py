import asyncio
import aioserial
import os
import asyncio
from src.api.shtrih import logger
from serial.tools import list_ports
from itertools import groupby
from src.api.shtrih.exceptions import *
from abc import ABC, abstractclassmethod
from typing import Any
from src.api.shtrih.protocol import ShtrihProto


class ShtrihDevice(ABC):

    @abstractclassmethod
    async def connect():
        pass

    @abstractclassmethod
    async def reconnect():
        pass
    
    @abstractclassmethod
    async def disconnect():
        pass

    @abstractclassmethod
    async def _read(cls, *args:Any):
        pass


    @abstractclassmethod
    async def _write(cls,*args:Any):
        pass


class ShtrihSerialDevice(ShtrihDevice, ShtrihProto):

    def __init__(self):
        super().__init__()
        self.connection = None
        self.port = os.environ.get("SHTRIH_SERIAL_PORT", "/dev/ttyUSB0")
        self.baudrate = int(os.environ.get("SHTRIH_SERIAL_BAUDRATE", "115200"))
        self.timeout = int(os.environ.get("SHTRIH_SERIAL_TIMEOUT", "2"))

    
    def discover(self):
        ports = list(list_ports.comports())
        if len(ports) > 1:
            hwids = [p[2].split(" ") for p in ports]  #type: ignore
            counter, group = [(len(list(group)), key)
                              for key, group in groupby(hwids)][0]
            if counter > 1:
                logger.error(
                    f"Discovered {counter} equal {group}. Recovering with default config"
                )
                return ShtrihSerialDevice().port
            else:
                return ports[0][0]
        elif len(ports) <= 0:
            raise SerialDeviceNotFound(f"Couldn't find any serial device")
        elif len(ports) == 1:
            return ports[0][0]

    async def connect(self):
        while not self.connection:
            try:
                port = self.discover()
                self.connection = aioserial.AioSerial(port=port,  #type: ignore
                                                    baudrate=self.baudrate, 
                                                    write_timeout=self.timeout, 
                                                    loop=asyncio.get_running_loop())
            except Exception as e:
                await logger.error(e)
                continue

    async def reconnect(self):
        if not self.connection.isOpen():
            await self.connect()
        else:
            self.connection.cancel_read()
            self.connection.cancel_write()
            self.connection.flush()
            self.connection = None
            await self.connect()
            
    async def disconnect(self):
        self.connection.cancel_read()
        self.connection.cancel_write()

    async def _read(self, size:int):
        data = await self.connection.read_async(size)
        return data

    async def _write(self, data:bytearray):
        await self.connection.write_async(data)


    async def serve(self):
        if self.connection.in_waiting >0:
            await self.consume()
        else:
            await asyncio.sleep(0.2)
    
        

