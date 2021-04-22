from datetime import timedelta
from src.api.webkassa.commands import WebkassaClientToken, WebkassaClientCloseShift
from src.db.models import States, Shift, Token
from src import logger, config
import asyncio
from tortoise import timezone
class Watchdog:

    def __init__(self):
        self.event = asyncio.Event()

    async def _check_shift(self):
        logger.debug('Checking shift')
        shift, states = await asyncio.gather(Shift.filter(id=1).first(), States.filter(id=1).first())
        if config['emulator']['shift']['close_by'] == 1: #close by counter
            asyncio.create_task(self._check_shift_by_counter(shift, states))
        elif config['emulator']['shift']['close_by'] ==2:
            asyncio.create_task(self._check_shift_by_time(shift))
        await asyncio.sleep(1)

    
    async def _check_shift_by_counter(self, shift, states):
        if config['emulator']['shift']['close_by'] == 'counter':
            period = timezone.now() - shift.open_date
            hours= int(period.total_seconds() // 3600)
            if (hours < 24
                and shift.total_docs == 0):
                if states.mode !=2:
                    await states.update_from_dict({'mode':2})
            elif hours >= 24:
                # closing shift for emulator status, no request to gateway
                if shift.total_docs ==0:
                    logger.warning('Autoclosing shift by timer. No documents in this shift')
                    await asyncio.gather(states.update_from_dict({'mode':2}),
                                        shift.update_from_dict.update({'open_date':timezone.now()}))
                else:
                    # if autclose enabled shift will be closed without printing report
                    if config['emulator']['shift']['autoclose']:
                        logger.warning('Autoclosing shift by timer')
                        await WebkassaClientCloseShift.handle()
                    else:
                        asyncio.ensure_future(logger.warning('Close shift manually. 24H elapsed'))
                        await States.filter(id=1).update(mode=3)

    async def _check_shift_by_time(self, shift):
        close_at = shift.open_date.time()+timedelta(hours=24)
        if timezone.now().time() >= close_at and shift.mode !=3:
            logger.warning('Autoclosing shift by timer')
            fut = asyncio.ensure_future(WebkassaClientCloseShift.handle())
            while not fut.done():
                await asyncio.sleep(0.2)
            if fut.exception():
                logger.warning('Autoclosing shift by timer: unsuccess')
            else:
                logger.warning('Autoclosing shift by timer: success')

    async def _token_check(self):
        logger.debug('Checking token')
        token_in_db = await Token.filter(id=1).get()
        if token_in_db.token =='' or (token_in_db.ts-timezone.now()).total_seconds()//3600 > 23:
            try:
                token = await WebkassaClientToken.handle()
                await Token.filter(id=1).update(
                                            token=token,
                                            ts=timezone.now())
            except:
                pass
        await asyncio.sleep(1)

    async def poll(self):
            tasks = []
            if config['emulator']['shift']['watchdog']:
                tasks.append(self._check_shift())
            if config['webcassa']['token']['watchdog']:
                tasks.append(self._token_check())
            if len(tasks) >0:
                while not self.event.is_set():
                    asyncio.ensure_future(asyncio.gather(*tasks))
        
        
    