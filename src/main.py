__version__ ='2.0.3'


import asyncio
from asyncio.locks import Event
import signal
import os
import uvloop
from src import logger, config
from src.db.connector import DBConnector
from src.db.models import Shift, States, Token
from src.api.printer.device import Printer
from src.api.shtrih.device import Paykiosk
from src.api.watchdog import Watchdog
from src.api.webkassa.commands import WebkassaClientToken


class Application:
    #instances
    db = DBConnector()
    printer = Printer()
    fiscalreg = Paykiosk()
    watchdog = Watchdog()
    event = Event()

    @classmethod
    async def signal_handler(cls, signal, loop):
        cls.printer.event.set()
        cls.fiscalreg.event.set()
        cls.watchdog.event.set()
        await logger.warning('Shutting down application')
        try:
            [task.cancel() for task in asyncio.all_tasks(loop)]
            await asyncio.wait_for(asyncio.gather(
                                                cls.printer.disconnect(),
                                                cls.fiscalreg.disconnect(),
                                                cls.db.disconnect()),1)
            await logger.shutdown()
        except:
            # perform eventloop shutdown
            try:
                loop.stop()
                loop.close()
            except:
                pass
        finally:
            os._exit(0)

    @classmethod
    async def _init_db(cls):
        try:
            # blocking step by step operations
            await logger.warning('Initializing DB')
            await asyncio.wait_for(cls.db.connect(),1)
        except asyncio.TimeoutError:
            await logger.error(f'Database connection issue')
            raise SystemExit(f'Emergency shutdown:Database connection issue')
        try:
            await asyncio.wait_for(asyncio.gather(Shift.get_or_create(id=1), States.get_or_create(id=1), Token.get_or_create(id=1)),1)
        except asyncio.TimeoutError:
            await logger.error(f'Database creating tables issue')
            raise SystemExit(f'Emergency shutdown: Creating database tables issue')


    @classmethod
    async def _init_printer(cls):
        logger.warning('Initializing printer')
        await cls.printer.connect()
        logger.warning('Printer initialized')

    @classmethod 
    async def _init_serial(cls):
        logger.warning('Initializing serial connection')
        await cls.fiscalreg.connect()
        logger.warning('Initializing serial connection done')


    @classmethod
    async def init(cls):
        await logger.warning(f'Initializing application. {__version__}')
        await cls._init_db()
        await logger.warning('Initializing devices')
        await cls._init_serial()
        asyncio.ensure_future(cls._init_printer())
        asyncio.ensure_future(WebkassaClientToken.handle())

    @classmethod
    async def serve(cls):
        await logger.warning('Application initialized.Serving')
        try:
            #background task: watchdog poller
            if config['emulator']['watchdog']:
                asyncio.create_task(cls.watchdog.poll())
            await cls.fiscalreg.poll()
        except Exception as e:
            raise SystemExit(f'Emergency shutdown: {e}')

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
   
   
   