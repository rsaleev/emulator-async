from src.api.webkassa.commands import WebkassaClientTokenCheck, WebkassaClientCloseShift
from src.db.models import States, Shift
from src import logger, config
import asyncio
from datetime import datetime

class Watchdog:

    @classmethod
    async def _check_shift(cls):
        shift = await Shift.get(id=1)
        period = datetime.now() - shift.open_date
        hours= int(period.total_seconds() // 3600)
        if (hours < 24
             and shift.total_docs == 0):
            await States.filter(id=1).update(mode=2)
        elif hours >= 24:
            if shift.total_docs ==0:
                shift_task = Shift.filter(id=1).update(open_date=datetime.now())
                states_task =States.filter(id=1).update(mode=2)
                await asyncio.gather(shift_task, states_task)
            else:
                if config['webkassa']['shift']['autoclose']:
                    log_task = logger.info(f'Autoclosing shift')
                    request_task = WebkassaClientCloseShift.handle()
                    await asyncio.gather(log_task, request_task)
                else:
                    await States.filter(id=1).update(mode=3)
    @classmethod
    async def poll(cls):
        asyncio.create_task(cls._check_shift())
        await asyncio.sleep(1)
    