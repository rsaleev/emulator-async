from src.api.printer.protocol import PrinterProto
from src.api.printer.command import PrinterCommand
from escpos.printer import Usb, USBNotFoundError
from usb.core import USBError, USBTimeoutError
from src.api.printer import logger
import os
import time

class UsbPrinter(PrinterProto):
    def __init__(self):
        super().__init__()
        self.device = None
      
    def discover(self):
        self.device = Usb(idVendor=int(os.environ.get('PRINTER_VENDOR_ID'),16), #type:ignore
                            idProduct=int(os.environ.get('PRINTER_PRODUCT_ID'),16), #type:ignore
                            in_ep=int(os.environ.get('PRINTER_IN_EP'),16), #type:ignore
                            out_ep=int(os.environ.get('PRINTER_OUT_EP'),16), #type:ignore
                            timeout=int(os.environ.get('PRINTER_TIMEOUT'))) #type:ignore
        if self.device:
            self.device.hw('INIT')
            PrinterCommand.set_device(self.device)
            PrinterCommand.set_buffer(self.buffer)
            return self.device
      

    def connect(self):
        while not self.device:
            try:
                self.discover()
            except Exception as e:
                time.sleep(3)
            else:
                logger.info('Connection to printing device established')
        self.device.profile.profile_data['media']['width']['pixels'] = int(os.environ.get("PRINTER_PAPER_WIDTH"), 540) #type:ignore

    def reconnect(self):
        self.device=None
        self.connect()
        
    def close(self):
        try:
            self.device.hw('INIT')
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
                output = self.device.device.read(self.device.in_ep, size, self.device.timeout) #type:ignore
                return output
            except (USBError, USBNotFoundError) as e:
                logger.exception(e)
                self.reconnect()
                continue
            except USBTimeoutError as e:
                logger.exception(e)
                self.reconnect()
                continue

    def _raw(self, data):
        while True:
            try:
                self.device.device.write(self.device.out_ep, data) #type:ignore
            except (USBError, USBNotFoundError) as e:
                logger.exception(e)
                self.reconnect()
                continue
            except USBTimeoutError as e:
                logger.exception(e)
                self.reconnect()
                continue

       
