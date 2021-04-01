import asyncio
from src.db.connector import DBConnector
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.webkassa.commands import WebkassaClientTokenCheck, WebkassaClientCloseShift
from src.api.printer.commands import PrinterFullStatusQuery
from src.db.models import States, Shift
from src import logger, config
from tortoise import timezone
import signal
import asyncio
import sys
import functools


class Application:
    printer = Printer()
    fiscalreg = Paykiosk()
    db = DBConnector()

    @classmethod
    async def _signal_cleanup(cls):
        await logger.warning('Shutting dow application')
        closing_tasks = []
        closing_tasks.append(cls.printer.disconnect())
        closing_tasks.append(cls.fiscalreg.disconnect())
        closing_tasks.append(cls.db.disconnect())
        await asyncio.gather(*closing_tasks, return_exceptions=True)
        await logger.shutdown()

    @classmethod
    async def _signal_handler(cls, signal, loop):

        tasks = [task for task in asyncio.all_tasks(loop) if task is not
                    asyncio.tasks.current_task()]
        for t in tasks:
            t.cancel()
        asyncio.ensure_future(cls._signal_cleanup())
        # perform eventloop shutdown
        try:
            loop.stop()
            loop.close()
        except:
            pass
        # close process
        sys.exit(0)

    @classmethod
    async def init(cls):
        loop = asyncio.get_running_loop()
        try:
            task_db_connect = cls.db.connect()
            task_fiscalreg_connect = cls.fiscalreg.connect()
            task_printer_connect = loop.run_in_executor(None, cls.printer.connect)
            await asyncio.gather(task_db_connect, task_fiscalreg_connect, task_printer_connect)
            await asyncio.gather(WebkassaClientTokenCheck.handle(),PrinterFullStatusQuery.handle())
        except Exception as e:
            await logger.exception(e)
    
    @classmethod
    async def poll(cls):
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
                    log_task = logger.info(f'Autoclosing shift')
                    request_task = WebkassaClientCloseShift.handle()
                    await asyncio.gather(log_task, request_task)
                else:
                    await States.filter(id=1).update(mode=4)
        await asyncio.sleep(1)
    
    @classmethod
    async def serve(cls):
        while True:
            await asyncio.ensure_future(cls.fiscalreg.serve())
            await asyncio.ensure_future(cls.poll())
        
            
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    app = Application()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    # add signal handler to loop
    for s in signals:
        loop.add_signal_handler(s, functools.partial(asyncio.ensure_future,
                                                        app._signal_handler(s, loop)))
    loop.run_until_complete(app.init())
    loop.run_until_complete(app.serve())
