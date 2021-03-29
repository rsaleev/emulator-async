from usb.core import USBError, USBTimeoutError
import os
import time
import usb
from src.api.printer.exceptions import * 


class UsbPrinter:
   
    def discover(self):
        device = usb.core.find(idVendor=int(os.environ.get('PRINTER_VENDOR_ID'),16), #type: ignore
                                idProduct=int(os.environ.get('PRINTER_PRODUCT_ID'),16))  #type: ignore
        if device is None:
            raise USBError("Device not found or cable not plugged in.")
        if device.backend.__module__.endswith("libusb1"): #type: ignore
            check_driver = None
            try:
                check_driver = device.is_kernel_driver_active(0) #type: ignore
            except NotImplementedError:
                pass
            if check_driver is None or check_driver:
                try:
                    device.detach_kernel_driver(0) #type: ignore
                except NotImplementedError:
                    pass
                except usb.core.USBError as e:
                    if check_driver is not None:
                        raise DeviceConnectionError("Could not detatch kernel driver: {0}".format(str(e)))
        try:
            device.set_configuration() #type: ignore
            device.reset() #type: ignore
        except usb.core.USBError as e:
            raise DeviceConnectionError("Could not set configuration: {0}".format(str(e)))
        finally:
            self.device = device
            return self.device

    def _read(self, size):
        try:
            output = self.device.read(int(os.environ.get('PRINTER_IN_EP'),16), size, int(os.environ.get('PRINTER_TIMEOUT'))) #type:ignore
            return output
        except Exception as e:
            raise DeviceIOError(e)

    def _write(self, data):
        try:
            self.device.write(int(os.environ.get('PRINTER_OUT_EP'),16), data) #type:ignore
        except Exception as e:
            raise DeviceIOError(e)
            
    def _disconnect(self):
        try:
            self.device.close() #type: ignore
        except Exception as e:
           pass



       
