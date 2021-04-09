from datetime import datetime
import asyncio
import struct
from dateutil import parser
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.webkassa.commands import WebkassaClientCloseShift
from src.db.models import States, Shift


class OpenShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x01,))
    _command_code = bytearray((0xE0,))
    
    @classmethod
    async def handle(cls, payload:bytearray):
        await asyncio.gather(cls._process(), cls._dispatch(payload))

    @classmethod
    async def _process(cls): 
        task_modify_state = States.filter(id=1).update(mode=2)
        task_modify_shift = Shift.filter(id=1).update(open_date=datetime.now(), total_docs=0)
        await asyncio.gather(task_modify_shift, task_modify_state)
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        return arr 

    @classmethod
    async def _dispatch(cls, payload:bytearray):
        pass

class CloseShift(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x05,))
    _command_code = bytearray((0xFF,0x43))

    @classmethod
    async def handle(cls, payload:bytearray):
        await asyncio.gather(cls._process(payload), cls._dispatch(payload))

    @classmethod
    async def _process(cls, payload:bytearray):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        res = await WebkassaClientCloseShift.handle()
        if res:
            shift_num = struct.pack('<2B', res.ShiftNumber,0)
            arr.extend(shift_num)
            shift_doc_num = struct.pack('<i',res.ReportNumber)
            arr.extend(shift_doc_num)
            fiscal_attribute = struct.pack('<i',res.CashboxIN)
            arr.extend(fiscal_attribute)
            api_dt = parser.parse(res.CloseOn)
            dt = struct.pack('<5B', api_dt.day, api_dt.month, api_dt.year%100, api_dt.hour, api_dt.minute)
            arr.extend(dt)
        else:
            shift_num = struct.pack('<2B', 0,0)
            arr.extend(shift_num)
            shift_doc_num = struct.pack('<i',0)
            arr.extend(shift_doc_num)
            fiscal_attribute = struct.pack('<i',0)
            arr.extend(fiscal_attribute)
            dt = struct.pack('<5B', datetime.now().day, datetime.now().month,datetime.now().year%100, datetime.now().hour, datetime.now().minute)
            arr.extend(dt)
        return arr

    @classmethod
    async def _dispatch(cls, payload:bytearray):
        pass

        