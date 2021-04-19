
import asyncio
import os
from src import config
from src.api.printer.commands.printing import PrintDeferredBytes
from src.api.printer.device import Printer
from src.db.models.state import States
from src.api.printer import logger
from src.api.printer.commands.present import CutPresent

class PrinterFullStatusQuery(Printer):

    alias = 'status'
    command = bytearray((0x10,0x04,0x14))
    device_type = os.environ.get('PRINTER_TYPE')

    @classmethod
    async def handle(cls, payload=None): 
        output = await cls._fetch_full_status()
        return output

    @classmethod
    async def _fetch_full_status(cls):
        await Printer().write(cls.command)
        await asyncio.sleep(0.5)
        output = False
        status = await Printer().read(6)
        if cls.device_type == 'SERIAL':
            status = bytearray(status) #type: ignore
        elif cls.device_type == 'USB':
            pass
        logger.debug(f'STATUS:{status}')
        paper= cls._set_paper_status(status[2])
        roll = cls._set_roll_status(status[2])
        cover = cls._set_cover_status(status[3])
        rec_err = cls._set_rec_status(status[4]) 
        unrec_err = cls._set_unrec_status(status[5])
        asyncio.ensure_future(logger.debug(
            f'PAPER:{int(paper)}|ROLL:{int(roll)}|COVER:{int(cover)}|RECOVERABLE:{int(rec_err)}|UNRECOVERABLE:{int(unrec_err)}'))
        # if paper not presented or cover is opened or unrecoverable/recoverable error exist -> submode=1
        if paper and not cover and not rec_err and not unrec_err:
            asyncio.ensure_future(States.filter(id=1).update(submode=0, paper=int(paper), cover=int(cover), roll=int(roll), jam=int(rec_err)))
            output = True
        # otherwise do not update submode value, assert that some operation in progress
        else:
            asyncio.ensure_future(States.filter(id=1).update(submode=1, paper=int(paper), cover=int(cover), roll=int(roll), jam=int(rec_err)))
        return output

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
    command = bytearray((0x10,0x04,0x11))
    device_type = os.environ.get('PRINTER_TYPE')


    @classmethod
    async def handle(cls):
        output = False
        await Printer().write(cls.command)
        status = await Printer().read(1)
        if cls.device_type == 'SERIAL':
            status = bytearray(status) #type: ignore
        elif cls.device_type == 'USB':
            pass
        output = cls._get_printing_status(status[0])
        return output

    @classmethod
    def _get_printing_status(cls, v:int):
        st = [int(elem) for elem in list(bin(v)[2:].zfill(8))] 
        print(st)
        if st[5] == 0:
            return True
        else:
            return False


class PrintBuffer(Printer):
  

    alias = 'buffer'

    CP866 = bytearray((0x17,))
    CP1251 = bytearray((0x46,))
    codepage_command = bytearray((0x1B,0x74))
    encoding_input = config['printer']['doc']['input']
    encoding_output = config['printer']['doc']['output']

    @classmethod
    async def handle(cls, payload=None):    
        if config['printer']['doc']['send_encoding']:
            codepage = bytearray()
            codepage.extend(cls.codepage_command)
            if cls.encoding_output == 'CP1251':
                codepage.extend(cls.CP1251)
            elif cls.encoding_output == 'CP866':
                codepage.extend(cls.CP866)
            Printer().buffer._raw(codepage) 
        await Printer().write(Printer().buffer.output)



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
class CheckPrinting(Printer):

    alias='aftercheck'

    @classmethod
    async def handle(cls):
        counts = 10
        n = 0 
        # check after printing errors
        while not Printer().event.is_set():
            after_printing_status = await PrintingStatusQuery.handle()
            # no errors: True
            if after_printing_status:
                # change submode=3: ready for next command 
                asyncio.ensure_future(States.filter(id=1).update(submode=3))
                Printer().buffer.clear()
                break
            else:
                if n == counts:
                    # set error status and clear dispenser/presenter
                    await asyncio.gather(States.filter(id=1).update(submode=1))
                    asyncio.create_task(cls._afterprint())
                    break
                else:
                    await asyncio.sleep(0.5)
                    n+=1
                    continue

    
    @classmethod
    async def _afterprint(cls):
        while not Printer().event.is_set():
            status = await PrinterFullStatusQuery.handle()
            if status:
                asyncio.ensure_future(States.filter(id=1).update(submode=2))
                await Printer().write(Printer().buffer.output)
                Printer().buffer.clear()
                await asyncio.gather(States.filter(id=1).update(submode=3),
                    CutPresent.handle())
                break
            else:
                await asyncio.sleep(0.5)
