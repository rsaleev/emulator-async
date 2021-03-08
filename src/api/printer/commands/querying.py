from src.protocols.printer.command import PrinterCommand
from src.devices.printer import PrinterDeviceProxy


class FullStatusQuery(PrinterCommand):
    _command_alias = 'full_status'
    _command_code = bytearray((0x10, 0x04, 0x14))
    _device = PrinterDeviceProxy()



    async def handle(cls):
        


        



