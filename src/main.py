import asyncio
import signal
import asyncio
import sys
import functools
from src import logger
from concurrent.futures import ThreadPoolExecutor
from src.db.connector import DBConnector
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.watchdog import Watchdog
from src.api.printer.commands import PrinterFullStatusQuery
from src.api.webkassa.commands import WebkassaClientTokenCheck


class Application:
    printer = Printer()
    fiscalreg = Paykiosk()
    db = DBConnector()
    watchdog = Watchdog()
    event = asyncio.Event()


    @classmethod
    async def _signal_handler(cls, signal, loop):
        await logger.warning('Shutting down application')
        cls.event.set()
        closing_tasks = []
        closing_tasks.append(cls.db.disconnect())
        closing_tasks.append(cls.printer.disconnect())
        closing_tasks.append(cls.fiscalreg.disconnect())
        try:
            await asyncio.gather(*closing_tasks, return_exceptions=True)     
            await loop.shutdown_default_executor()
            await logger.warning('Finalizing...')
            await logger.shutdown()
            [task.cancel() for task in asyncio.all_tasks(loop)]
            # perform eventloop shutdown
            loop.stop()
            loop.close()
        except:
            pass
        # close process
        sys.exit(0)

    @classmethod
    def _exception_handler(cls, loop, context):
        loop.stop()
        loop.close()
        raise SystemExit(f'Stopping loop due to error: {context["exception"]}')


    @classmethod
    async def init(cls):
        await logger.warning('Initializing application...')
        executor = ThreadPoolExecutor(max_workers=5)
        loop = asyncio.get_running_loop()
        loop.set_default_executor(executor)
        loop.set_exception_handler(handler=cls._exception_handler)

        try:
            task_db_connect = cls.db.connect()
            task_fiscalreg_connect = cls.fiscalreg.connect()
            task_printer_connect = loop.run_in_executor(None, cls.printer.connect)
            await task_printer_connect
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
        while not cls.event.is_set():
            try:
                await asyncio.ensure_future(cls.fiscalreg.poll())
                await asyncio.ensure_future(cls.watchdog.poll())
            except Exception as e:
                await logger.exception(e)
                cls.event.set()
                raise SystemExit('Emergency shutdown.Check logs')


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
    