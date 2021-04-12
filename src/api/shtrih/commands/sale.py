import asyncio
import struct
from uuid import uuid4
from tortoise.functions import Max
from src import config
from typing import Tuple, Coroutine
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
    async def handle(cls, payload:bytearray) ->bytearray:
        try:
            count = struct.unpack('<iB',payload[4:9])[0]//10**3
            price = struct.unpack('<iB', payload[9:14])[0]//10**2
            tax_percent = config['webkassa']['taxgroup'][str(payload[14])]
            tax = round(price*count/(100+int(tax_percent))*tax_percent,2)
            receipt = await Receipt.filter(ack=False).annotate(max_value = Max('id')).first()
            if receipt.id: #type: ignore
                await Receipt.filter(id=receipt.id).update(count=count, price=price, tax_percent=tax_percent, tax=tax) #type:ignore
            # create record with empty ticket number
            else:
                await Receipt.create(uid=uuid4(), ticket='', count=count, price=price, tax_percent=tax_percent, tax=tax)
           
        except Exception as e:
            asyncio.create_task(logger.exception(e))
            cls.set_error(3)
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 


class OpenReceipt(ShtrihCommand, ShtrihCommandInterface):
    # TODO: TEST
    _length = bytearray((0x03,))
    _command_code = bytearray((0x8D,))

    @classmethod
    def handle(cls) -> Tuple[Coroutine, Coroutine]:
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
    def handle(cls, payload:bytearray) -> Tuple[Coroutine, Coroutine]:
        task_process = cls._process()
        task_execute = cls._dispatch()
        return task_process, task_execute


    @classmethod
    async def _process(cls):
        try:
            await States.filter(id=1).update(gateway=1)
        except Exception as e:
            asyncio.ensure_future(logger.exception(e))
            cls.set_error(3)
        else:
            cls.set_error(0)
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
    async def handle(cls, payload:bytearray):
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
        receipt = await Receipt.filter(ack=False).annotate(max_value = Max('id')).first()
        if payment >0 and receipt.id :
            change = bytearray(struct.pack('<iB', (payment-receipt.price)*10**2,0)) #type: ignore
            await Receipt.filter(id=receipt.id).update(payment_type = payment_type, payment=payment)
            receipt_updated = Receipt.get(id=receipt.id)
            response =  await WebkassaClientSale.handle(receipt_updated)
            if not response:
                cls.set_error(0x03)
            else:
                cls.set_error(0x00) 
        else:
            asyncio.create_task(logger.error('No payment data'))
            cls.set_error(0x03)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        arr.extend(change)
        return arr 
        



    
