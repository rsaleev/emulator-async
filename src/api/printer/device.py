from src.api.printer.protocol import PrinterProto
from src.api.printer.command import PrinterCommand
from usb.core import USBError, USBTimeoutError
from src.api.printer import logger
import os
import time
import usb


class UsbPrinter(PrinterProto):
    def __init__(self):
        super().__init__()
        self.device = None
        self.id_vendor = int(os.environ.get('PRINTER_VENDOR_ID'),16)
        self.id_product=int(os.environ.get('PRINTER_PRODUCT_ID'),16)
        self.in_ep=int(os.environ.get('PRINTER_IN_EP'),16)
        self.out_ep=int(os.environ.get('PRINTER_OUT_EP'),16)
        self.timeout=int(os.environ.get('PRINTER_TIMEOUT'))
      
    def discover(self):
        self.device = usb.core.find(idVendor=self.id_vendor, idProduct=self.id_product)
        if self.device is None:
            raise USBError("Device not found or cable not plugged in.")
        self.idVendor = self.device.idVendor
        self.idProduct = self.device.idProduct
        if self.device.backend.__module__.endswith("libusb1"):
            check_driver = None
            try:
                check_driver = self.device.is_kernel_driver_active(0)
            except NotImplementedError:
                pass

            if check_driver is None or check_driver:
                try:
                    self.device.detach_kernel_driver(0)
                except NotImplementedError:
                    pass
                except usb.core.USBError as e:
                    if check_driver is not None:
                        raise USBError("Could not detatch kernel driver: {0}".format(str(e)))

        try:
            self.device.set_configuration()
            self.device.reset()
        except usb.core.USBError as e:
            print("Could not set configuration: {0}".format(str(e)))
        finally:
            return self.device

    def connect(self):
        while not self.device:
            try:
                self.discover()
            except Exception as e:
                logger.exception(e)
                time.sleep(3)
            else:
                logger.info('Connection to printing device established')
        self.profile.profile_data['media']['width']['pixels'] = int(os.environ.get("PRINTER_PAPER_WIDTH", 540)) #type:ignore

    def reconnect(self):
        self.device=None
        self.connect()
        
    def close(self):
        try:
            self.hw('INIT')
            self.device.close()
        except:
            pass

    def read(self, size:int):
        """method for reading incoming data from usb port

        Args:
            size (int): number of bytes to read

        Returns:
            List[int]: array of bytes converted to int
        """
        while True:
            try:
                output = self.device.read(self.in_ep, size, self.timeout) #type:ignore
                return output
            except (USBError, USBTimeoutError) as e:
                logger.exception(e)
                self.reconnect()
                continue

    def _read(self):
        pass

    def _raw(self, data):
        while True:
            try:
                self.device.write(self.out_ep, data) #type:ignore
                break
            except (USBError, USBTimeoutError) as e:
                logger.exception(e)
                self.reconnect()
                continue

    def write(self, data): 
        while True:
            try:
                self.device.write(self.out_ep, data) #type:ignore
                break
            except (USBError, USBTimeoutError) as e:
                logger.exception(e)
                self.reconnect()
                continue

printer = UsbPrinter()

       
