import asyncio
import signal
import asyncio
import os
import uvloop
from functools import partial
from src import logger
from concurrent.futures import ThreadPoolExecutor
from src.db.connector import DBConnector
from src.db.models import Shift, States, Token
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.watchdog import Watchdog
from src.api.printer.commands import PrinterFullStatusQuery
from src.api.webkassa.commands import WebkassaClientToken


class Application:
    #instances
    db = DBConnector()
    printer = Printer()
    fiscalreg = Paykiosk()
    watchdog = Watchdog()


    @classmethod
    async def signal_handler(cls, signal, loop):
        cls.printer.event.set()
        cls.fiscalreg.event.set()
        cls.watchdog.event.set()
        await logger.warning('Shutting down application')
        try:
            await asyncio.wait_for(cls.db.disconnect(),0.5)
            cls.printer.disconnect()
            cls.fiscalreg.disconnect()
        except:
            [task.cancel() for task in asyncio.all_tasks(loop)]
            # perform eventloop shutdown
            try:
                loop.stop()
                loop.close()
            except:
                pass
            os._exit(0)


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
    async def serve(cls):
        try:
            await cls.fiscalreg.poll()
            #background task: watchdog poller
            asyncio.create_task(cls.watchdog.poll())
        except Exception as e:
            logger.exception(e)
            raise SystemExit(f'Emergency shutdown')

    @classmethod
    def run(cls):
        # ASYNCIO LOOP POLICY
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.new_event_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(s, lambda:asyncio.ensure_future(cls.signal_handler(s, loop)))
        loop.run_until_complete(cls.init())
        loop.run_until_complete(cls.serve())
        loop.run_forever()

if __name__ == '__main__':
    Application.run()
   
   
   