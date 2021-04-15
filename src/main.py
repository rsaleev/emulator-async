import asyncio
import signal
import asyncio
from src.api.printer.commands.querying import ClearBuffer
import sys
import uvloop
from src import logger
from concurrent.futures import ThreadPoolExecutor
from src.db.connector import DBConnector
from src.db.models import Shift, States, Token
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.watchdog import Watchdog
from src.api.printer.commands import PrinterFullStatusQuery, PrintBuffer, CutPresent, PrintQR, PrintBytes
from src.api.webkassa.commands import WebkassaClientToken

from escpos.printer import Usb

class Application:
    #asyncio 
    event = asyncio.Event()
    #instances
    db = DBConnector()
    printer = Printer()
    fiscalreg = Paykiosk()
    watchdog = Watchdog()


    @classmethod
    async def _signal_handler(cls, signal, loop):
        cls.printer.event.set()
        cls.fiscalreg.event.set()
        cls.watchdog.event.set()
        cls.event.set()
        await logger.warning('Shutting down application')
        closing_tasks = []
        closing_tasks.append(cls.db.disconnect())
        closing_tasks.append(cls.printer.disconnect)
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
    async def init(cls):
        await logger.warning('Initializing application...')
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        loop.set_default_executor(executor)
        try:
            # blocking step by step operations
            await logger.warning('Initializing DB')
            await cls.db.connect()
            await Shift.get_or_create(id=1) 
            await States.get_or_create(id=1)            
            await logger.warning('Initializing gateway')
            token = await WebkassaClientToken.handle()
            await Token.get_or_create(id=1, token=token)
            await logger.warning('Initializing devices')
            await cls.printer.connect()
            await PrinterFullStatusQuery.handle()
            await cls.fiscalreg.connect()
        except Exception as e:
            await logger.exception(e)
            raise SystemExit('Emergency shutdown')
        else:
            await logger.warning('Application initialized.Serving')

    @classmethod
    async def run(cls):
        while not cls.event.is_set():
            try:
                await cls.fiscalreg.poll()
                #background task: watchdog poller
                asyncio.create_task(cls.watchdog.poll())
            except Exception as e:
                await logger.exception(e)
                raise SystemExit(f'Emergency shutdown')

if __name__ == '__main__':
    # ASYNCIO LOOP POLICY
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.new_event_loop()
    app = Application()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    # add signal handler to loop
    for s in signals:
        loop.add_signal_handler(s, lambda: asyncio.ensure_future(app._signal_handler(s, loop)))
    loop.run_until_complete(app.init())
    loop.run_until_complete(app.run())
    loop.run_forever()
   