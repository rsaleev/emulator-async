import asyncio
from datetime import datetime
from src.db.connector import DBConnector
from src.api.printer.device import UsbPrinter
from src.api.shtrih.device import ShtrihSerialDevice
from src.api.webkassa.commands import WebkassaClientTokenCheck, WebkassaClientCloseShift
from src.api.printer.commands import PrinterFullStatusQuery
from src.db.models import States, Shift
from src import logger, config
import sys

class Application:
    printer = UsbPrinter()
    fiscalreg = ShtrihSerialDevice()
    connector = DBConnector()

    @classmethod
    async def init(cls):
        loop = asyncio.get_running_loop()
        try:
            task_db_connect = cls.connector.connect()
            task_fiscalreg_connect = cls.fiscalreg.connect()
            task_printer_connect = loop.run_in_executor(None, cls.printer.connect)
            await asyncio.gather(task_db_connect, task_fiscalreg_connect, task_printer_connect)
            await asyncio.gather(WebkassaClientTokenCheck.handle(),PrinterFullStatusQuery.handle())
        except Exception as e:
            await logger.exception(e)
            sys.exit(1)
    
    @classmethod
    async def poll(cls):
        shift = await Shift.get(id=1)
        state = await States.get(id=1)
        period = datetime.now() - shift.open_date
        hours= int(period.total_seconds() // 3600)
        minutes = int((period.total_seconds() % 3600) //60)
        seconds = int((period.total_seconds() % 3600) % 60)
        if (hours < 23 and minutes < 59 and seconds <59
             and state.mode !=2
             and shift.total_docs == 0):
            await States.filter(id=1).update(mode=2)
        elif (hours > 23 and minutes > 59 and seconds >=  59 
            and state.mode !=2 
            and shift.total_docs ==0):
            shift_task = Shift.filter(id=1).update(open_date=datetime.now())
            states_task =States.filter(id=1).update(mode=2)
            await asyncio.gather(shift_task, states_task)
        elif (hours >23 and minutes >59 and seconds >=59 
            and shift.total_docs>0):
            await States.filter(id=1).update(mode=4)
            if config['webkassa']['shift']['autoclose']:
                log_task = logger.info(f'Autoclosing shift')
                request_task = WebkassaClientCloseShift.handle()
                await asyncio.gather(log_task, request_task)
        
    
    @classmethod
    async def serve(cls):
        while True:
            try:
                if cls.fiscalreg.connection.in_waiting > 0:
                    await cls.fiscalreg.consume()
                else:
                    await cls.poll()
            except Exception as e:
                await logger.exception(e)
            finally:
                await asyncio.sleep(0.2)
            
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    app = Application()
    loop.run_until_complete(app.init())
    loop.run_until_complete(app.serve())
    loop.run_forever()





    


