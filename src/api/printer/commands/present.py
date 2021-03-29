from src.api.printer.device import Printer
from src import config
from src.db.models.state import States
import asyncio

class CutPresent(Printer):


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
            Printer()._raw(cls.cut)  #type: ignore
            Printer()._raw(cls.eject)  #type: ignore
            Printer().hw('INIT') #type: ignore
        else:        
            Printer()._raw(cls.cut)  #type: ignore
            present_len_to_bytes = int(config['printer']['receipt']['present_length_mm']/7.3).to_bytes(1, 'little')
            Printer()._raw(cls.present.extend(present_len_to_bytes))  #type: ignore
            Printer().hw('INIT') #type: ignore
        Printer().buffer.clear()  #type: ignore
        