
import asyncio
import struct
from datetime import datetime
from src.api.shtrih.command import ShtrihCommand, ShtrihCommandInterface
from src.api.printer.commands import PrinterFullStatusQuery
from src.api.webkassa.commands import WebkassaClientTokenCheck
from src.db.models import States
from src.api.shtrih.device import Paykiosk
from bitarray import bitarray #type: ignore
class FullState(ShtrihCommand, ShtrihCommandInterface):

    _length = bytearray((0x30,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x11,)) #B[2] - 1 byte
    _fw_version = struct.pack('<2B', 0x43, 0x31) #B[5,6] - 2 bytes -> CP1251
    _fw_build = struct.pack('<H', 0x01) #B[7,8] - 2 bytes - LittleEndian
    _fw_date = struct.pack('<3B',0x03, 0x0C,0x14) #B[9,10,11] - 3 bytes - BigEndian
    _sale_num = struct.pack('<B', 0x01) #B[12] - 1 byte
    _doc_num = struct.pack('<H', 0x00) #B[13, 14] - 2 bytes - LittleEndian
    _mode = struct.pack('<B', 0x02) # DEFAULT MODE B[17]
    _submode = struct.pack('<B', 0x00) # DEFAULT MODE B[18]
    _port = struct.pack('<B', 0x00)
    _printer_fw_version = struct.pack('2B', 0x4E, 0x41) #B[19,20]
    _printer_fw_build = struct.pack('<H', 0x00) #B[21,22]
    _printer_fw_date = struct.pack('<3B', 0x01, 0x01, 0x10) #B[23,24,25]
    _printer_flags = struct.pack('<B', 0x00) #B[32]
    _factory_num = struct.pack('<I', int.from_bytes(bytes(bytearray((0x3C, 0x11, 0x00, 0x00))), byteorder='little')) # B[33,34,35,36]
    _last_shift_num = struct.pack('<H', 0x00) #[37,38,39,40]
    _free_records = struct.pack('<H', 0x00) #[41,42]
    _reregistrations = struct.pack('<B', 0x00) #[43]
    _left_reregistrations = struct.pack('<B', 0x00) #[44]
    _inn = struct.pack('<6B', 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
        
    # SETTERS 
    @classmethod
    def set_date(cls) -> bytes:
        return struct.pack('<3B',datetime.now().day, datetime.now().month, datetime.now().year%100)
        
    @classmethod
    def set_time(cls) -> bytes:
        return struct.pack('<3B', datetime.now().hour, datetime.now().minute, datetime.now().second)

    @classmethod
    def set_sale_num(cls, arg:int=0) -> bytes:
        # TODO fetch sale number from DB
        return struct.pack('<1B', arg)

    @classmethod
    def set_doc_num(cls, arg:int=0) -> bytes:
        # TODO fetch doc_num from DB
        return struct.pack('<H', arg)

    @classmethod
    def set_flags(cls,states:States) -> bytes:
        flags = struct.pack(
            '<H',
            int.from_bytes(bitarray(
                [states.paper,0, 0, 1, 0, 0, states.roll, 0, states.cover, states.cover, states.jam,0,0,0,1,0]).tobytes(),
                           byteorder='little'))
        return flags
    
    @classmethod
    def set_mode(cls, arg:int) -> bytes:
        return bytearray(struct.pack('<B', arg))

    @classmethod
    def set_submode(cls, arg:int) -> bytes:
        return bytearray(struct.pack('<B', arg))   

    @classmethod
    async def handle(cls, payload) -> asyncio.Task:
        return asyncio.create_task(asyncio.gather(cls._process(), cls._dispatch()))

    @classmethod
    async def _process(cls) -> bytearray:
        task_printer_check = PrinterFullStatusQuery.handle()
        task_token_check = WebkassaClientTokenCheck.handle()
        await asyncio.gather(task_printer_check, task_token_check)
        states = await States.get(id=1)
        mode = states.mode
        if states.gateway == 0:
            mode = 4
            cls.set_error(0x11)
        ### response body
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        arr.extend(cls._fw_version)
        arr.extend(cls._fw_build)
        arr.extend(cls._fw_date)
        arr.extend(cls.set_sale_num())
        arr.extend(cls.set_doc_num())
        arr.extend(cls.set_flags(states)) #type:ignore
        arr.extend(cls.set_mode(mode)) #type:ignore
        arr.extend(cls.set_submode(states.submode)) #type:ignore
        arr.extend(cls._port)
        arr.extend(cls._printer_fw_version)
        arr.extend(cls._printer_fw_build)
        arr.extend(cls._printer_fw_date)
        arr.extend(cls.set_date())
        arr.extend(cls.set_time())
        arr.extend(cls._printer_flags)
        arr.extend(cls._factory_num)
        arr.extend(cls._last_shift_num)
        arr.extend(cls._free_records)
        arr.extend(cls._reregistrations)
        arr.extend(cls._left_reregistrations)
        arr.extend(cls._inn)
        return arr

    @classmethod
    async def _dispatch(cls) -> None:
        pass

