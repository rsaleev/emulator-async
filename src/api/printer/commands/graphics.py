import struct
import asyncio
from PIL import Image, ImageOps
from src import config
from src.api.printer.device import Printer
from src.api.printer import logger 

class PrintQR(Printer):

    alias = 'qr'
    size = config['printer']['qr']['size']

    @classmethod
    async def handle(cls, payload:str):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cls._print_qr, payload)

    @classmethod
    def _print_qr(cls, payload:str):
        Printer().hw('INIT')
        Printer().qr(content=payload, center=True, size=cls.size)
        Printer().hw('INIT')

        
class PrintGraphicLines(Printer):

    alias = 'graphics'
    impl = config['printer']['barcode']['impl']
    center = config['printer']['barcode']['center']
    
    @classmethod
    async def handle(cls, payload:bytearray):
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, cls._print_graphics, payload)
        except Exception as e:
            logger.exception(e)
            raise e

    @classmethod
    def _print_graphics(cls, payload:bytearray):
        Printer().hw('INIT')
        arr = struct.unpack(f'<{len(payload)}B', payload)[6:66]
        img = Image.frombytes(data=bytes(arr), size=(len(arr)*8,1), mode='1')
        repeats = struct.unpack('<2B', payload[4:6])[0]
        bc = Image.new(mode='1', size=(len(arr)*8, repeats))
        for i in range(0,repeats):
            bc.paste(img, (0,i))
        bc_inverted = ImageOps.invert(bc.convert('L'))
        Printer().image(bc_inverted, impl=cls.impl, center=cls.center)
        Printer().hw('INIT')

     

     