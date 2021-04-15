from datetime import timedelta
from src.api.webkassa.commands import WebkassaClientToken, WebkassaClientCloseShift
from src.db.models import States, Shift, Token
from src import logger, config
import asyncio
from tortoise import timezone
class Watchdog:

    @classmethod
    async def _check_shift(cls):
        shift, states = await asyncio.gather(Shift.filter(id=1).first(), States.filter(id=1).first())
        if config['emulator']['shift']['close_by'] == 1: #close by counter
            await cls._check_shift_by_counter(shift, states)
        elif config['emulator']['shift']['close_by'] ==2:
            await cls._check_shift_by_time(shift, states)
        await asyncio.sleep(1)

    @classmethod
    async def _check_shift_by_counter(cls, shift, states):
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
                    asyncio.ensure_future(logger.warning('Autoclosing shift by timer. No documents in this shift'))
                    await asyncio.gather(states.update_from_dict({'mode':2}),
                                        shift.update_from_dict.update({'open_date':timezone.now()}))
                else:
                    # if autclose enabled shift will be closed without printing report
                    if config['emulator']['shift']['autoclose']:
                        asyncio.ensure_future(logger.warning('Autoclosing shift by timer'))
                        await WebkassaClientCloseShift.handle()
                    else:
                        asyncio.ensure_future(logger.warning('Close shift manually. 24H elapsed'))
                        await States.filter(id=1).update(mode=3)

    @classmethod
    async def _check_shift_by_time(cls, shift, states):
        close_at = shift.open_date.time()+timedelta(hours=24)
        if timezone.now().time() >= close_at and shift.mode !=3:
            asyncio.ensure_future(logger.warning('Autoclosing shift by timer'))
            await WebkassaClientCloseShift.handle()        


    @classmethod
    async def _token_check(cls):
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

    @classmethod
    async def poll(cls):
        if config['emulator']['shift']['watchdog']:
            asyncio.create_task(cls._check_shift())
        asyncio.create_task(cls._token_check())
        
        
    