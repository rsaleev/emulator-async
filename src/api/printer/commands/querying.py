from src.api.printer.command import PrinterCommand
from src.db.models.state import States
from src.api.printer import logger
import asyncio
import time
class PrinterFullStatusQuery(PrinterCommand):

    alias = 'status'
    command = bytearray((0x10,0x04,0x14))


    @classmethod
    async def handle(cls, payload=None): 
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(None, cls._fetch_full_status)
            paper, cover, rec_err, unrec_err = result
            await States.filter(id=1).update(paper=int(paper), cover=int(cover), jam=int(rec_err))
            if paper and not cover and not rec_err and not unrec_err:
                await States.filter(id=1).update(submode=0)
            else:
                await States.filter(id=1).update(submode=1) 
        except:
            await States.filter(id=1).update(submode=1) 

    @classmethod
    def _fetch_full_status(cls):
        cls.device.write(cls.command)
        status = cls.device.read(6) 
        logger.debug(f'STATUS:{status}')
        paper = cls._set_paper_status(status[2])
        cover = cls._set_cover_status(status[3])
        rec_err = cls._set_rec_status(status[4]) 
        unrec_err = cls._set_unrec_status(status[5])
        states = (paper, cover, rec_err, unrec_err)
        return states
        
    @classmethod
    def _set_paper_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]
        if st[7] ==1:
            return False
        else:
            return True

    @classmethod
    def _set_cover_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))] 
        if (st[7]+st[6])!=0:
            return True
        else:
            return False

    @classmethod
    def _set_rec_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]  
        if st[1] !=0:
            return True
        else:
            return False

    @classmethod
    def _set_unrec_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]  
        if min(st) !=0:
            return True
        else:
            return False

class PrintingStatusQuery:

    alias = 'online'
    command = bytearray((0x10,0x04,0x02))

    @classmethod
    def handle(cls, payload=None):
        cls.device.write(cls.command) #type: ignore
        status = cls.device.read(6) #type: ignore
        output = cls._get_printing_status(status[2])
        return output

    @classmethod
    def _get_printing_status(cls, v:int):
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))] 
        if st[5] == 0 or st[6] ==0:
            return True
        else:
            return False 
class PrintBuffer:

    alias = 'buffer'
    cut = bytearray((0x1B,0x69))
    eject = bytearray((0x1D,0x65,0x05))

    @classmethod
    async def handle(cls, payload=None):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls.device._raw, cls.buffer.output)  #type: ignore
        # check if printing completed with success
        status = await loop.run_in_executor(None, PrintingStatusQuery.handle)
        # clear buffer after success
        if status:
            cls.buffer.clear()  #type: ignore
        # printing ended unsuccessfully
        else:
            # cut and eject 
            await loop.run_in_executor(None, cls.device._raw, cls.cut) #type: ignore
            await loop.run_in_executor(None, cls.device._raw, cls.eject) #type: ignore
            await loop.run_in_executor(None, cls._poll_for_recover)  #type: ignore

    @classmethod
    def _poll_for_recover(cls):
        while True:
            time.sleep(0.2)
            status = PrintingStatusQuery.handle()
            if status:
                cls.device._raw(cls.buffer.output) #type: ignore
                break
            else:
                time.sleep(0.2)
                continue

class ClearBuffer:

    alias = 'clear'

    @classmethod
    async def handle(cls, payload=None):
        cls.buffer.clear()  #type: ignore