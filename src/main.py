import asyncio
from src.db.connector import DBConnector
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.watchdog import Watchdog
from src.api.printer.commands import PrinterFullStatusQuery
from src.api.webkassa.commands import WebkassaClientTokenCheck
from src import logger
import signal
import asyncio
import sys
import functools


class Application:
    printer = Printer()
    fiscalreg = Paykiosk()
    db = DBConnector()
    watchdog = Watchdog()

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
        await logger.warning('Initializing application...')

        loop = asyncio.get_running_loop()
        try:
            task_db_connect = cls.db.connect()
            task_fiscalreg_connect = cls.fiscalreg.connect()
            task_printer_connect = loop.run_in_executor(None, cls.printer.connect)
            await asyncio.gather(task_db_connect, task_fiscalreg_connect, task_printer_connect)
            task_printer_check = PrinterFullStatusQuery.handle()
            task_webkassa_check = WebkassaClientTokenCheck.handle()
            await asyncio.gather(task_printer_check, task_webkassa_check)
        except Exception as e:
            await logger.exception(e)
        else:
            await logger.warning('Application initialized')

   
    @classmethod
    async def serve(cls):
        await logger.info('Serving...')
        while True:
            try:
                await asyncio.ensure_future(cls.fiscalreg.serve())
                await asyncio.ensure_future(cls.watchdog.poll())
            except Exception as e:
                await logger.exception(e)

        
            
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
    