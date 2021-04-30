
import asyncio
import os
from binascii import hexlify
from src import config
from src.api.printer.exceptions import * 
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
        output = False
        await Printer().write(cls.command)
        if cls.device_type == 'SERIAL':
            raw = await Printer().read(6)
            status = bytearray(raw) #type: ignore
        elif cls.device_type == 'USB':
            await asyncio.sleep(0.5)
            status = await Printer().read(40)
        try:
            logger.debug(f'STATUS:{status}') #type: ignore
            paper= cls._set_paper_status(status[2])#type: ignore
            roll = cls._set_roll_status(status[2]) #type: ignore
            cover = cls._set_cover_status(status[3]) #type: ignore
            rec_err = cls._set_rec_status(status[4]) #type: ignore
            unrec_err = cls._set_unrec_status(status[5]) #type: ignore
            logger.debug(
                f'PAPER:{int(paper)}|ROLL:{int(roll)}|COVER:{int(cover)}|RECOVERABLE:{int(rec_err)}|UNRECOVERABLE:{int(unrec_err)}')
            # if paper not presented or cover is opened or unrecoverable/recoverable error exist -> submode=1
            if paper and not cover and not rec_err and not unrec_err:
                asyncio.ensure_future(States.filter(id=1).update(submode=0, 
                                                                    paper=int(paper), 
                                                                    cover=int(cover), 
                                                                    roll=int(roll), 
                                                                    jam=int(rec_err)))
                output = True
            else:
                asyncio.ensure_future(States.filter(id=1).update(submode=1, 
                                                                    paper=int(paper), 
                                                                    cover=int(cover), 
                                                                    roll=int(roll), 
                                                                    jam=int(rec_err)))
        except:
            pass
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
    command = bytearray((0x10,0x04,0x02))
    device_type = os.environ.get('PRINTER_TYPE')


    @classmethod
    async def handle(cls):
        output = False
        await Printer().write(cls.command)
        if cls.device_type == 'SERIAL':
            raw = await Printer().read(1)
            status = bytearray(raw) #type: ignore
        elif cls.device_type == 'USB':
            await asyncio.sleep(0.5)
            status = await Printer().read(40)
        logger.debug(
                f'AFTERPRINT:{status}') #type: ignore
        output = cls._get_printing_status(status[2]) #type: ignore
        return output

    @classmethod
    def _get_printing_status(cls, v:int):
        try:
            st = [int(elem) for elem in list(bin(v)[2:].zfill(8))] 
            logger.debug(
                    f'AFTERPRINT BITS:{st}') #type: ignore
            if st[5] == 0:
                return True
            else:
                return False
        except Exception as e:
            logger.error(e)
            return False


class PrintBuffer(Printer):
  
    alias = 'buffer'

    @classmethod
    async def _recover(cls):
        logger.warning('Waiting for paper feed')
        while not Printer.event.is_set():
            status = await PrinterFullStatusQuery.handle()
            logger.debug(f'Afterprint check full status:{status}')
            if status:
                asyncio.ensure_future(States.filter(id=1).update(submode=3))
                break
            else:
                await asyncio.sleep(0.5)
                continue
                        
    @classmethod
    async def _check(cls):
        # get status of last operation
        check = await PrintingStatusQuery.handle()
        logger.debug(f'Printed issues:{check}')
        # no errors
        if check:
            return True
        # printing stopped due paper end
        else:
            # set submode=2 - paper not present (active)
            await States.filter(id=1).update(submode=2)
            # check for recover
            rec_fut = asyncio.ensure_future(cls._recover())
            while not rec_fut.done():
                # sleep until paper feeder notify
                await asyncio.sleep(0.5)
            if not rec_fut.exception():
                # present failed document and continue
                await CutPresent.handle()
                return True
            else:
                logger.error(rec_fut.exception())
                return False           


    @classmethod
    async def handle(cls, payload=None):
        await States.filter(id=1).update(submode=5)
        while not Printer().event.is_set():
            # print buffer
            await Printer().write(Printer().buffer.output)
            logger.debug(f'Printing buffer:{hexlify(Printer().buffer.output, sep=":")}')
            # check operation result for errors
            if config['printer']['receipt']['ensure']:
                r = asyncio.ensure_future(cls._check())
                while not r.done():
                    await asyncio.sleep(0.5)                        
                if r.result():
                    # reprint buffer
                    await Printer().write(Printer().buffer.output)
                    break
            else:
                break

class ClearBuffer(Printer):

    alias = 'clear'

    @classmethod
    async def handle(cls, payload=None):
        Printer().buffer.clear()

class ModeSetter(Printer):

    alias ='mode'
    command = bytearray((0x1D, 0x65, 0x14))

    @classmethod
    async def handle(cls):
        Printer()._raw(cls.command)


