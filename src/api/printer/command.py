
from src.api.command import AbstractCommand
from src.devices.printer import PrinterDeviceProxy

class PrinterCommand(AbstractCommand):
    device = PrinterDeviceProxy()
    
class PrinterCommandInterface:
    pass