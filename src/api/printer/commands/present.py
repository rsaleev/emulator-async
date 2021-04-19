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
    async def handle(cls):
        await asyncio.gather(cls._present(),States.filter(id=1).update(submode=0))
        
    @classmethod
    async def _present(cls):
        """_present 

        Performs document (receipt) presentation:

        Modes: eject/present with length

        """

        try:
            # cut ticket (left in printer presenter)
            await Printer().write(cls.cutting)  
            if config['printer']['presenter']['eject']:
                # eject
                await Printer().write(cls.eject)  
            else:        
                # present ticket with length parameter
                present_mode = bytearray()
                present_mode.extend(cls.present)
                present_mode.append(cls.present_length)
                await Printer().write(present_mode) #type: ignore PyLance
        except Exception as e:
            await logger.exception(e)
             
