from src.api.printer.device import Printer
from src import config
from src.db.models.state import States
import asyncio
from src.api.printer import logger

class CutPresent(Printer):


    alias = 'cut'

    cut = bytearray((0x1B,0x69))
    eject = bytearray((0x1D,0x65,0x05))
    present = bytearray((0x1D,0x65,0x03))

    @classmethod
    async def handle(cls, payload=None):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls._present)
        await States.filter(id=1).update(submode=0)
        
    @classmethod
    def _present(cls):
        try:
            if config['printer']['receipt']['eject']:
                Printer()._raw(cls.cut)  #type: ignore
                Printer().hw('INIT') #type: ignore
                Printer()._raw(cls.eject)  #type: ignore
            else:        
                Printer()._raw(cls.cut)  #type: ignore
                Printer().hw('INIT') #type: ignore
                Printer()._raw(cls.present.append(int(config['printer']['receipt']['present_length_mm']/7.3)))  #type: ignore
        except Exception as e:
            logger.exception(e)
