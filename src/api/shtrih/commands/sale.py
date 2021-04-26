import asyncio
from re import S
import struct
from uuid import uuid4
from tortoise.functions import Max
from src import config
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt
from src.db.models.state import States
from src.api.webkassa.commands import WebkassaClientSale
from src.api.shtrih import logger
from src.api.printer.commands import ClearBuffer, PrintDeferredBytes

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
            if not config['webkassa']['receipt']['header']:
                asyncio.ensure_future(ClearBuffer.handle())
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


class OpenReceipt(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x8D,))

    @classmethod
    async def handle(cls, payload) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 

class CancelReceipt(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x88,))

    @classmethod
    async def handle(cls, payload:bytearray) -> bytearray:
        try:
            await States.filter(id=1).update(gateway=1)
        except Exception as e:
            logger.exception(e)
            cls.set_error(3)
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr 
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
            await receipt.update_from_dict({'payment_type':payment_type, 'payment':payment})
            asyncio.ensure_future(receipt.save())
            asyncio.ensure_future(States.filter(id=1).update(mode=8))
            asyncio.create_task(PrintDeferredBytes.handle())
            try:
                await WebkassaClientSale.handle(receipt)
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



class OpenSale2(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x01,))
    _command_code = bytearray((0xFF,0x46))

    @classmethod
    async def handle(cls, payload:bytearray) ->bytearray:
        try:
            count = struct.unpack('<i2B',payload[5:11])[0]//10**6
            price = struct.unpack('<iB', payload[11:16])[0]//10**2
            tax_percent = config['webkassa']['taxgroup'][str(payload[26])]
            tax = round(price*count/(100+int(tax_percent))*tax_percent,2)
            receipt = await Receipt.filter(ack=False).annotate(max_value = Max('id')).first()
            if receipt.id: #type: ignore
                await Receipt.filter(id=receipt.id).update(count=count, price=price, tax_percent=tax_percent, tax=tax) #type:ignore
            # create record with empty ticket number
            else:
                await Receipt.create(uid=uuid4(), ticket='', count=count, price=price, tax_percent=tax_percent, tax=tax)
            if not config['webkassa']['receipt']['header']:
                asyncio.ensure_future(ClearBuffer.handle())
        except Exception as e:
            asyncio.ensure_future(logger.exception(e))
            cls.set_error(3)
        else:
            cls.set_error(0)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        return arr 
        
class CloseReceipt2(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x08,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x8E, )) #B[2] - 1 byte

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
            await receipt.update_from_dict({'payment_type':payment_type, 'payment':payment})
            asyncio.ensure_future(receipt.save())
            asyncio.ensure_future(States.filter(id=1).update(mode=8))
            asyncio.create_task(PrintDeferredBytes.handle())
            try:
                await WebkassaClientSale.handle(receipt)
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




    
