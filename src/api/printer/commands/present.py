from src.api.printer.device import Printer
from src import config
from src.db.models.state import States
import asyncio
from src.api.printer import logger


class CutPresent(Printer):

    alias = 'cut'
    cutting = bytearray((0x1B,0x69))
    eject = bytearray((0x1D,0x65,0x05))
    present = bytearray((0x1D,0x65,0x03))
    present_length = int(config['printer']['presenter']['present_length_mm']/7.3)

    @classmethod
    async def handle(cls, payload=None):
        await asyncio.gather(cls._present(),States.filter(id=1).update(submode=0))
        
    @classmethod
    async def _present(cls):
        try:
            if config['printer']['presenter']['eject']:
                await Printer().write(cls.cutting)  
                await Printer().write(cls.eject)  
            else:        
                await Printer().write(cls.cutting)
                present_mode = cls.present.append(cls.present_length)
                await Printer().write(present_mode) #type: ignore PyLance
        except Exception as e:
            logger.exception(e)
            raise e 
