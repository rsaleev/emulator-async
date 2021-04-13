import os
import time
import usb
import aioserial
import asyncio
from itertools import groupby
from serial.serialutil import SerialException, SerialTimeoutException
from src.api.shtrih import logger
from serial.tools import list_ports
from src import config
from src.api.device import *
from escpos.printer import Dummy
from src.api.printer.protocol import PrinterProto
from src.api.printer import logger, async_logger

class UsbDevice(DeviceImpl):

    device = None
    connected = False

    @classmethod
    def _open(cls):
        cls.device = usb.core.find(
            idVendor=int(os.environ.get('PRINTER_VENDOR_ID'),
                         16),  #type: ignore
            idProduct=int(os.environ.get('PRINTER_PRODUCT_ID'),
                          16))  #type: ignore
        if cls.device is None:
            raise DeviceConnectionError(
                "Device not found or cable not plugged in.")
        if cls.device.backend.__module__.endswith("libusb1"):  #type: ignore
            check_driver = None
            try:
                check_driver = cls.device.is_kernel_driver_active(
                    0)  #type: ignore
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
    def _read(cls, size):
        try:
            output = cls.device.read(
                int(os.environ.get('PRINTER_IN_EP'), 16), size,#type:ignore
                int(os.environ.get('PRINTER_TIMEOUT')))  #type:ignore
            return output
        except (usb.core.USBError, usb.core.USBTimeoutError, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    def _write(cls, data):
        try:
            cls.device.write(int(os.environ.get('PRINTER_OUT_EP'), 16),#type:ignore
                             data)  #type:ignore
        except (usb.core.USBError, usb.core.USBTimeoutError, IOError) as e:
            raise DeviceIOError(e)

    @classmethod
    def _close(cls):
        try:
            usb.util.dispose_resources(cls.device)
        except:
            pass

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
                await async_logger.error(f"Found multiple devices {counter} with same group {group}")
            else:
                port = ports[0][0]
        elif len(ports) == 0:
            await async_logger.error(f"Device not found with autodiscover connecting with default params")
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

class Printer(PrinterProto, Device):
    
    buffer = Dummy()

    def __init__(self):
        PrinterProto.__init__(self)
        self._impl = None
        self.discover()

    def discover(self):
        if os.environ['PRINTER_TYPE'] == 'USB':
            self._impl = UsbDevice()
        elif os.environ['PRINTER_TYPE'] == 'SERIAL':
            self._impl = SerialDevice()
        return self._impl

    def connect(self):
        logger.info(f'Connecting to printer device...')
        if self._impl:
            while not self._impl.connected:
                try:
                    self._impl._open()
                except DeviceConnectionError as e:
                    logger.error(e)
                    time.sleep(1)
                    continue
                else:
                    logger.info('Connection to printer established')
                    self.profile.profile_data['media']['width']['pixels'] = int(
                        os.environ.get("PRINTER_PAPER_WIDTH", 540))  #type:ignore
                    if config['printer']['continuous_mode']:
                        self._raw(bytearray((0x1D, 0x65, 0x14)))
                    return self.device
        else:
            logger.error('Implementation not found')

    def reconnect(self):
        if self._impl:
            self._impl.connected = False
            self.connect()

    def disconnect(self):
        self.hw('INIT')
        self._impl._close()

    def read(self, size: int):
        while True:
            try:
                output = self._impl._read(size)
                return output
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue

    def _raw(self, msg):
        while True:
            try:
                self._impl._write(msg)
                break
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue

    def write(self, data):
        while True:
            try:
                self._impl._write(data)
                break
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue
