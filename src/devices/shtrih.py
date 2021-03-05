from src.devices.device import AbstractDevice
import asyncio
import aioserial
import os
import asyncio


class ShtrihSerialDevice(AbstractDevice):
    def __init__(self):
        self._device = None
        self._port = '/dev/ttyUSB0'
        self._baudrate = 115200
        self._buffer = asyncio.Queue()


    async def discover(self):
        pass

    async def connect(self):
        self._device = aioserial.AioSerial(port=self._port, baudrate=self._baudrate, loop=asyncio.get_running_loop())
        return self._device

    async def reconnect(self):
        if not self._device.isOpen():
            await self.connect()
        else:
            self._device.cancel_read()
            self._device.cancel_write()
            self._device.flush()
            
    async def disconnect(self):
        pass

    async def write(self, data:bytearray) ->None:
        await self._device.write_async(data)

    async def read(self, size:int=None) -> bytearray:
        print(self._device.dsr)
        print(self._device.dtr)
        print(self._device.cts)
        if not size:
            return bytearray(await self._device.read_async(self._device.in_waiting))
        else:
            return bytearray(await self._device.read_async(size))

    
