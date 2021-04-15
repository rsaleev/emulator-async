
import asyncio
from src.api.printer.commands.printing import PrintDeferredBytes
import time
from functools import partial
from src.api.printer.device import Printer
from src.db.models.state import States
from src.api.printer import logger


class PrinterFullStatusQuery(Printer):

    alias = 'status'
    command = bytearray((0x10,0x04,0x20,))

    @classmethod
    async def handle(cls, payload=None): 
        output = await cls._fetch_full_status()
        return output

    @classmethod
    async def _fetch_full_status(cls):
        await Printer().write(cls.command) 
        status = await Printer().read(6)
        logger.debug(f'STATUS:{status}')
        paper= cls._set_paper_status(status[2])
        roll = cls._set_roll_status(status[2])
        cover = cls._set_cover_status(status[3])
        rec_err = cls._set_rec_status(status[4]) 
        unrec_err = cls._set_unrec_status(status[5])
        asyncio.ensure_future(logger.debug(
            f'PAPER:{int(paper)}|ROLL:{int(roll)}|COVER:{int(cover)}|RECOVERABLE:{int(rec_err)}|UNRECOVERABLE:{int(unrec_err)}'))
        # if paper not presented or cover is opened or unrecoverable/recoverable error exist -> submode=1
        if not paper or cover or rec_err and not unrec_err:
            asyncio.ensure_future(States.filter(id=1).update(submode=1, paper=int(paper), cover=int(cover), roll=int(roll), jam=int(rec_err)))
            return False
        # otherwise do not update submode value, assert that some operation in progress
        else:
            asyncio.ensure_future(States.filter(id=1).update(paper=int(paper), cover=int(cover), roll=int(roll), jam=int(rec_err)))
            return True

    @classmethod
    def _set_paper_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]
        return not st[7]

    @classmethod
    def _set_roll_status(cls, v:int) ->int:
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))]
        return not st[5]            

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
    command = bytearray((0x10,0x04,0x02,))

    @classmethod
    async def handle(cls):
        await Printer().write(cls.command)
        status = await Printer().read(6) 
        output = cls._get_printing_status(status[0])
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
        # clear buffer to prevent conflict 
        # enter loop for 
        while 1:
            # check current printer status: if ready -> True
            status = await PrinterFullStatusQuery.handle()
            if status:
                # print buffered data
                # pre-printing op: get data from deferred storage and put in buffer
                await Printer().write(Printer().buffer.output)
                # check after printing errors
                after_printing_status = await PrintingStatusQuery.handle()
                # no errors: True
                if after_printing_status:
                    # change submode=3: ready for next command 
                    asyncio.ensure_future(States.filter(id=1).update(submode=3))
                    break
                # errors: False
                else:
                    # set error status and clear dispenser/presenter
                    await asyncio.gather(States.filter(id=1).update(submode=1),
                                    loop.run_in_executor(None, partial(Printer().cut, True)))
                    await asyncio.sleep(0.1)
                    continue
            else:
                # wait until next iteration, possibly wait for a long time
                await asyncio.sleep(1)
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
