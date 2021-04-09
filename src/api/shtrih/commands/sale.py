import asyncio
import struct
from uuid import uuid4
from src import config
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt
from src.db.models.state import States
from src.api.printer.commands import ClearBuffer
from src.api.webkassa.commands import WebkassaClientSale
from src.api.shtrih import logger

class OpenSale(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x80,))

    @classmethod
    async def handle(cls, payload:bytearray):
        return asyncio.create_task(asyncio.gather(cls._process(), cls._dispatch(payload)))

    @classmethod
    async def _process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 

    @classmethod
    async def _dispatch(cls, payload:bytearray) ->None:
        count = struct.unpack('<iB',payload[4:9])[0]//10**3
        price = struct.unpack('<iB', payload[9:14])[0]//10**2     
        tax_percent = config['webkassa']['taxgroup'][str(payload[14])]
        tax = round(price*count/(100+int(tax_percent))*tax_percent,2)
        # check if record of ticket exists
        receipt = await Receipt.get_or_none()
        if receipt:
            await Receipt.filter(uid=receipt.uid).update(count=count, price=price, tax_percent=tax_percent, tax=tax)
        # create record with empty ticket number
        else:
            await Receipt.create(uid=uuid4(), ticket='', count=count, price=price, tax_percent=tax_percent, tax=tax)
        if not config['webkassa']['receipt']['header']:
            await ClearBuffer.handle()

class OpenReceipt(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x8D,))

    @classmethod
    async def handle(cls):
        task_process = cls._process()
        task_execute = cls._dispatch()
        return task_process, task_execute


    @classmethod
    async def _process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 

    @classmethod
    async def _dispatch(cls) ->None:
        pass

class CancelReceipt(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x88,))

    @classmethod
    async def handle(cls, payload:bytearray):
        await asyncio.gather(cls._process(), cls._dispatch())


    @classmethod
    async def _process(cls):
        task_cancel_receipt =  Receipt.filter(ack=False).delete()
        task_modify_states = States.filter(id=1).update(gateway=1)
        await asyncio.gather(task_cancel_receipt, task_modify_states)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 


    @classmethod
    async def _dispatch(cls) ->None:
        pass

class SimpleCloseSale(ShtrihCommand, ShtrihCommandInterface):
    
    _length = bytearray((0x08,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x85,)) #B[2] - 1 byte

    @classmethod
    async def handle(cls, payload:bytearray) -> asyncio.Task:
        return asyncio.create_task(asyncio.gather(cls._process(payload), cls._dispatch()))

    @classmethod
    async def _process(cls, payload:bytearray):
        change = bytearray((0x00,0x00,0x00,0x00,0x00))
        payment_type = 0
        payment = 0
        cash = struct.unpack('<iB', payload[4:9])[0]//10**2
        cc = struct.unpack('<iB', payload[9:14])[0]//10**2
        if cash >0:
            payment = cash
        elif cc >0:
            payment = cc
            payment_type = 1
        else:
            cls.set_error(0x03)
        if payment:
            receipt = await Receipt.get_or_none()
            change = bytearray(struct.pack('<iB', (payment-receipt.price)*10**2,0))
            await Receipt.filter(uid=receipt.uid).update(payment_type=payment_type, payment=payment)
            if config['emulator']['post_sale']:
                try:
                    await WebkassaClientSale.handle()
                except:
                    cls.set_error(0x03)
                else:
                    cls.set_error(0x00)
        else:
            asyncio.ensure_future(logger.error('No payment data'))
            cls.set_error(0x03)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        arr.extend(change)
        return arr 
        
    @classmethod
    async def _dispatch(cls):
        if not config['emulator']['post_sale']:
            await asyncio.create_task(WebkassaClientSale.handle())
        



    
