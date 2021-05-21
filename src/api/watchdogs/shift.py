import asyncio
from src import config
from datetime import datetime
from tortoise import timezone
from src.db.models import States, Shift
from src.api.watchdogs import logger
from src.api.webkassa.commands import WebkassaClientCloseShift

class ShiftWatchdog:

    def __init__(self):
        self.event = asyncio.Event()        

    
    async def _check_shift_by_counter(self, shift, states):
        period = timezone.now() - shift.open_date
        hours= int(period.total_seconds() // 3600)
        if (hours < 24 and shift.total_docs == 0):
            if states.mode !=2:
                states.update_from_dict({'mode':2})
                await states.save()
        elif hours >= 24:
            # closing shift for emulator status, no request to gateway
            if shift.total_docs ==0:
                logger.warning('Autoclosing shift by timer. No documents in this shift')
                states.update_from_dict({'mode':2}),
                shift.update_from_dict({'open_date':timezone.now()})
                await asyncio.gather(
                                    states.save(),
                                    shift.save())
            else:
                # if autclose enabled shift will be closed without printing report
                if config['emulator']['shift']['autoclose']:
                    logger.warning('Autoclosing shift by timer')
                    fut = asyncio.ensure_future(WebkassaClientCloseShift.handle())
                    while not fut.done():
                        await asyncio.sleep(0.2)
                    if fut.exception():
                        logger.warning('Autoclosing shift by timer: unsuccess')
                    else:
                        logger.warning('Autoclosing shift by timer: success')
                else:
                    logger.warning('Close shift manually. 24H elapsed')
                    states.update_from_dict({'mode':3})
                    await states.save()


    async def _check_shift_by_time(self, shift,states):
        close_at = datetime.strptime(config['emulator']['shift']['close_at'], "%H:%M:%S")
        close_at_today = shift.open_date.replace(hour=close_at.hour, minute=close_at.minute, second=close_at.second)
        delta = (timezone.now()-close_at_today).total_seconds()
        if -1 <=delta <=1 and states.mode !=3:
            logger.warning('Autoclosing shift by timer')
            fut = asyncio.ensure_future(WebkassaClientCloseShift.handle())
            while not fut.done():
                await asyncio.sleep(0.2)
            if fut.exception():
                logger.warning('Autoclosing shift by timer: unsuccess')
            else:
                logger.warning('Autoclosing shift by timer: success')
            await asyncio.sleep(1)

   

    async def poll(self):
        while not self.event.is_set():
            logger.debug('Checking shift')
            fut = asyncio.ensure_future(asyncio.gather(Shift.filter(id=1).first(), States.filter(id=1).first()))
            while not fut.done():
                await asyncio.sleep(0.2)
            if not fut.exception():
                shift, states = fut.result()
                if config['emulator']['shift']['close_by'] == 1: #close by counter
                    asyncio.create_task(self._check_shift_by_counter(shift, states))
                elif config['emulator']['shift']['close_by'] ==2:
                    asyncio.create_task(self._check_shift_by_time(shift, states))
            await asyncio.sleep(1)

          