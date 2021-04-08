from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
import struct
from src.db.models import Receipt
from src.api.shtrih.device import Paykiosk
import asyncio
class SubTotal(ShtrihCommand, ShtrihCommandInterface, Paykiosk):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x89,))

    @classmethod
    async def handle(cls, payload) -> asyncio.Task:
        return asyncio.create_task(asyncio.gather(cls._process(), cls._dispatch()))

    @classmethod
    async def _process(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        receipt = await Receipt.get_or_none()
        if receipt:
            cls.set_error(0x00)
            subtotal = bytearray(struct.pack('<iB', receipt.price*10**2, 0))
            arr.extend(subtotal)
        else:
            cls.set_error(0x35)
            arr.extend(bytearray((0x00,0x00,0x00,0x00,0x00)))
        return arr

    @classmethod
    async def _dispatch(cls) -> None:
        pass
