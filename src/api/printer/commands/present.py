from src.api.printer.command import PrinterCommand
from src import config
from src.db.models.state import States
import asyncio

class CutPresent(PrinterCommand):


    alias = 'cut'

    cut = bytearray((0x1B,0x69))
    eject = bytearray((0x1D,0x65,0x05))
    present = bytearray((0x1D,0x65,0x03))

    @classmethod
    async def handle(cls, payload=None):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls._present)

    @classmethod
    def _present(cls):
        if config['printer']['receipt']['eject']:
            cls.device._raw(cls.cut)  #type: ignore
            cls.device._raw(cls.eject)  #type: ignore
            cls.device.hw('INIT') #type: ignore
        else:        
            cls.device._raw(cls.cut)  #type: ignore
            present_len_to_bytes = int(config['printer']['receipt']['present_length_mm']/7.3).to_bytes(1, 'little')
            cls.device._raw(cls.present.extend(present_len_to_bytes))  #type: ignore
            cls.device.hw('INIT') #type: ignore
        cls.buffer.clear()  #type: ignore
        