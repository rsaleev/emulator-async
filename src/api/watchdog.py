from src.api.webkassa.commands import WebkassaClientToken, WebkassaClientCloseShift
from src.db.models import States, Shift, Token
from src import logger, config
import asyncio
from tortoise import timezone
class Watchdog:

    @classmethod
    async def _check_shift(cls):
        shift = await Shift.get(id=1)
        period = timezone.now() - shift.open_date
        hours= int(period.total_seconds() // 3600)
        if (hours < 24
             and shift.total_docs == 0):
            await States.filter(id=1).update(mode=2)
        elif hours >= 24:
            if shift.total_docs ==0:
                shift_task = Shift.filter(id=1).update(open_date=timezone.now())
                states_task =States.filter(id=1).update(mode=2)
                await asyncio.gather(shift_task, states_task)
            else:
                if config['webkassa']['shift']['autoclose']:
                    await WebkassaClientCloseShift.handle()
                else:
                    await States.filter(id=1).update(mode=3)
        await asyncio.sleep(1)

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
        asyncio.create_task(cls._check_shift())
        asyncio.create_task(cls._token_check())
        
        
    