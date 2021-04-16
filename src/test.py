import asyncio
import signal
import asyncio
import os
import uvloop
from src import logger
from src.db.connector import DBConnector
from src.db.models import Shift, States, Token
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.watchdog import Watchdog
from src.api.printer.commands import PrinterFullStatusQuery
from src.api.webkassa.commands import WebkassaClientToken


class Application:
    #asyncio 
    event = asyncio.Event()
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
        cls.event.set()
        await logger.warning('Shutting down application')
        try:
            await asyncio.wait_for(cls.db.disconnect(),0.5)
            cls.printer.disconnect()
            #await cls.fiscalreg.disconnect()
        except:
            await loop.shutdown_default_executor()
            [task.cancel() for task in asyncio.all_tasks(loop)]
            await loop.shutdown_default_executor
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
        try:
            # blocking step by step operations
            await logger.warning('Initializing DB')
            await cls.db.connect()
            await Shift.get_or_create(id=1) 
            await States.get_or_create(id=1)            
            await logger.warning('Initializing gateway')
            await cls.printer.connect()
            await PrinterFullStatusQuery.handle()
        except Exception as e:
            await logger.exception(e)
            raise SystemExit('Emergency shutdown')
        else:
            await logger.warning('Application initialized.Serving')

    @classmethod
    async def serve(cls):
        while not cls.event.is_set():
            try:
                await cls.fiscalreg.poll()
                #background task: watchdog poller
                asyncio.create_task(cls.watchdog.poll())
            except Exception as e:
                await logger.exception(e)
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
        loop.run_forever()

if __name__ == '__main__':
    Application.run()
   
   
   