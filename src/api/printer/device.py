from src.api.printer.protocol import PrinterProto
from src.api.printer import logger
import os
import time
from src.api.device import *
from escpos.printer import Dummy
from src import config
import usb


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


class Printer(PrinterProto, Device):
    def __init__(self):
        super().__init__()
        self.impl = None
        self.buffer = Dummy()
        self.discover()

    def discover(self):
        if os.environ['PRINTER_TYPE'] == 'USB':
            self.impl = UsbDevice()
        elif os.environ['PRINTER_TYPE'] == 'SERIAL':
            raise NotImplementedError
        return self.impl

    def connect(self):
        logger.info(f'Connecting to printer device...')
        while not self.impl.connected:
            try:
                self.impl._open()
            except DeviceConnectionError as e:
                logger.error(e)
                time.sleep(3)
                continue
            else:
                logger.info('Connection to printer established')
                self.profile.profile_data['media']['width']['pixels'] = int(
                    os.environ.get("PRINTER_PAPER_WIDTH", 540))  #type:ignore
                if config['printer']['continuous_mode']:
                    self._raw(bytearray((0x1D, 0x65, 0x14)))
                return self.device

    def reconnect(self):
        self.impl.connected = False
        self.connect()

    def disconnect(self):
        self.hw('INIT')
        self.impl._close()

    def read(self, size: int):
        while True:
            try:
                output = self.impl._read(size)
                return output
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue

    def _raw(self, msg):
        while True:
            try:
                self.impl._write(msg)
                break
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue

    def write(self, data):
        while True:
            try:
                self.impl._write(data)
                break
            except (DeviceConnectionError, DeviceIOError):
                self.reconnect()
                continue
