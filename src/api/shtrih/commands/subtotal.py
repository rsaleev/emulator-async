import struct
import asyncio
from tortoise.functions import Max

from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.db.models import Receipt


class SubTotal(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x89,))

    @classmethod
    async def handle(cls, payload):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        receipt = await Receipt.filter(ack=False).annotate(max_value = Max('id')).first()
        if receipt:
            cls.set_error(0x00)
            subtotal = bytearray(struct.pack('<iB', receipt.price*10**2, 0))
            arr.extend(subtotal)
        else:
            cls.set_error(0x35)
            arr.extend(bytearray((0x00,0x00,0x00,0x00,0x00)))
        return arr

