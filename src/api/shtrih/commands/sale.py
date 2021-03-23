from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models.receipt import Receipt
from src.db.models.state import States
import asyncio
import struct
from src import config
from uuid import uuid4
from src.api.printer.commands import ClearBuffer
from datetime import datetime
from src.api.webkassa.commands import WebkassaClientSale

class OpenSale(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x80,))

    @classmethod
    async def handle(cls, payload)->None:
        tasks = [cls.process(), cls.dispense(payload)]
        await asyncio.gather(*tasks)

    @classmethod
    async def process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        await cls.send(arr)

    @classmethod
    async def dispense(cls, payload) ->None:
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
    async def handle(cls, payload)->None:
        tasks = [cls.process()]
        await asyncio.gather(*tasks)

    @classmethod
    async def process(cls)-> None:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        await cls.send(arr)

    @classmethod
    def dispense(cls) ->None:
        pass

class CancelReceipt(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x88,))

    @classmethod
    async def handle(cls, payload:bytearray)->None:
        tasks = [cls.process()]
        await asyncio.gather(*tasks)

    @classmethod
    async def process(cls):
        # pre
        Receipt.filter(ack=False).delete()
        await States.filter(id=1).update(gateway=1)
        # post
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls, payload:bytearray) ->None:
        pass

class SimpleCloseSale(ShtrihCommand, ShtrihCommandInterface):
    
    _length = bytearray((0x03,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x85,)) #B[2] - 1 byte
    _weblink = bytearray((ord('N'), ord('/'), ord('A')))

    @classmethod
    async def handle(cls, payload) -> None:
        if config['emulator']['post_sale']:
            try:
                await cls.dispense(payload)
            except:
                cls.set_error(0x03)
            else:
                cls.set_error(0x00)
            finally:
                await cls.process()
        else:
            tasks = [cls.process(), cls.dispatch]
            await asyncio.gather(*tasks)

    @classmethod
    async def process(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        arr.extend(cls._weblink)
        await cls.send(arr)

    @classmethod
    async def dispatch(cls, payload):
            await cls._set_sale(payload)
            await WebkassaClientSale.handle()

    @classmethod
    async def _set_sale(cls, payload):
        receipt = await Receipt.get_or_none()
        if receipt:
            payment_type = 0
            payment = 0
            cash = struct.unpack('<iB', payload[4:9])[0]//10**2
            cc = struct.unpack('<iB', payload[9:14])[0]//10**2
            if cash >0:
                payment = cash
            elif cc >0:
                payment = cc
                payment_type = 1
            await Receipt.filter(uid=receipt.uid).update(payment_type=payment_type, payment=payment, payment_ts=datetime.now())

        



    
