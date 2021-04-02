from src.api.printer.device import Printer
from src.db.models.state import States
from src.api.printer import logger
import asyncio
import time


class PrinterFullStatusQuery(Printer):

    alias = 'status'
    command = bytearray((0x10,0x04,0x14))

    @classmethod
    async def handle(cls, payload=None): 
        loop = asyncio.get_running_loop()
        try:
            paper, roll, cover, rec_err, unrec_err = await loop.run_in_executor(None, cls._fetch_full_status)
            await States.filter(id=1).update(paper=int(paper), cover=int(cover), roll=int(roll), jam=int(rec_err))
            if not paper and not roll and not cover and not rec_err and not unrec_err:
                await States.filter(id=1).update(submode=0)
            else:
                await States.filter(id=1).update(submode=1) 
        except Exception as e:
            logger.exception(e)
            await States.filter(id=1).update(submode=1) 

    @classmethod
    def _fetch_full_status(cls):
        Printer().write(cls.command) #type: ignore
        status =Printer().read(6) #type: ignore
        logger.debug(f'STATUS:{status}')
        paper= cls._set_paper_status(status[2])
        roll = cls._set_roll_status(status[2])
        cover = cls._set_cover_status(status[3])
        rec_err = cls._set_rec_status(status[4]) 
        unrec_err = cls._set_unrec_status(status[5])
        return paper, roll, cover, rec_err, unrec_err


        
    @classmethod
    def _set_paper_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]
        return ~st[7]

    @classmethod
    def _set_roll_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]
        return ~st[5]            

    @classmethod
    def _set_cover_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))] 
        return st[7]+st[6]
       

    @classmethod
    def _set_rec_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]  
        return st[1]

    @classmethod
    def _set_unrec_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]  
        return min(st)

class PrintingStatusQuery(Printer):

    alias = 'online'
    command = bytearray((0x10,0x04,0x02))

    @classmethod
    def handle(cls, payload=None):
        Printer().write(cls.command)
        status = Printer().read(6) 
        output = cls._get_printing_status(status[2])
        return output

    @classmethod
    def _get_printing_status(cls, v:int):
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))] 
        if st[5] == 0 or st[6] ==0:
            return True
        else:
            return False 
class PrintBuffer(Printer):

    alias = 'buffer'
    cut = bytearray((0x1B,0x69))
    eject = bytearray((0x1D,0x65,0x05))

    @classmethod
    async def handle(cls, payload=None):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, Printer()._raw,Printer().buffer.output)  
        status = await loop.run_in_executor(None, PrintingStatusQuery.handle)
        # clear buffer after success
        if status:
            Printer().buffer.clear()  
        # printing ended unsuccessfully
        else:
            # cut and eject 
            await loop.run_in_executor(None, Printer()._raw, cls.cut) #type: ignore
            await loop.run_in_executor(None, Printer()._raw, cls.eject) #type: ignore
            await loop.run_in_executor(None, cls._poll_for_recover)  #type: ignore

    @classmethod
    def _poll_for_recover(cls):
        while True:
            time.sleep(0.2)
            status = PrintingStatusQuery.handle()
            if status:
                Printer()._raw(Printer().buffer.output) 
                break
            else:
                time.sleep(0.2)
                continue

class ClearBuffer(Printer):

    alias = 'clear'

    @classmethod
    async def handle(cls, payload=None):
        Printer().buffer.clear()

class ModeSetter(Printer):

    alias ='mode'
    command = bytearray((0x1D, 0x65, 0x14))

    @classmethod
    async def handle(cls, payload=None):
        Printer()._raw(cls.command)
