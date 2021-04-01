from src.api.printer.device import Printer
import struct
from PIL import Image
from src import config
import asyncio

class PrintQR(Printer):

    alias = 'qr'
    size = config['printer']['qr']['size']


    @classmethod
    async def handle(cls, payload:str):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls._print_qr, payload)

    @classmethod
    def _print_qr(cls, payload:str):
        Printer().qr(content=payload, center=True, size=cls.size)
        
class PrintGraphicLines(Printer):

    alias = 'graphics'
    
    impl = config['printer']['barcode']['impl']


    @classmethod
    async def handle(cls, payload:bytearray):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls._print_graphics, payload)


    @classmethod
    def _print_graphics(cls, payload:bytearray):
        arr = struct.unpack(f'<{len(payload)}B', payload)[15:55]
        img = Image.frombytes(data=bytes(arr), size=(len(arr)*8,1), mode='1')
        repeats = struct.unpack('<2B', payload[4:6])[0]
        bc = Image.new(mode='1', size=(len(arr)*8, repeats))
        for i in range(0,repeats):
            bc.paste(img, (0,i))
        Printer().image(bc, center=True, impl=cls.impl)  
     
