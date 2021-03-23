from src.api.printer.device import UsbPrinter
from src.api.printer.command import PrinterCommand
from src.api.shtrih.device import ShtrihSerialDevice



printer = UsbPrinter()
PrinterCommand.set_buffer(printer.buffer)
PrinterCommand.set_device(printer.device)


shtrih = ShtrihSerialDevice()





