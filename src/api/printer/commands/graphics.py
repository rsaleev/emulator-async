import struct
from PIL import Image, ImageOps
from src import config
from src.api.printer.device import Printer
from src.api.printer import logger

class PrintQR(Printer):

    alias = 'qr'
    size = config['printer']['qr']['size']

    @classmethod
    async def handle(cls, payload:str):
        Printer().buffer.qr(content=payload, center=True, size=cls.size)


class PrintGraphicLines(Printer):

    alias = 'graphics'
    impl = config['printer']['barcode']['impl']
    center = config['printer']['barcode']['center']
    
    @classmethod
    async def handle(cls, payload:bytearray):
        """handle 

        Generate image of barcode from bytes.
        
        Sequence of bytes must follow barcode protocol ordering e.g. CODE128C, Aztec and etc.

        Args:
            payload (bytearray): incoming raw data from Fiscal device
        """
        logger.debug('Rendering graphics')
        try:
            arr = struct.unpack(f'<{len(payload)}B', payload)[6:66]
            # generates 1 pixel heigth image
            img = Image.frombytes(data=bytes(arr), size=(len(arr)*8,1), mode='1')
            # pixel data is repeated several times
            repeats = struct.unpack('<2B', payload[4:6])[0]
            # prepare new image
            bc = Image.new(mode='1', size=(len(arr)*8, repeats))
            # append 1 px data several times (repeats)
            for i in range(0,repeats):
                bc.paste(img, (0,i))
            # invert colors black/white
            bc_inverted = ImageOps.invert(bc.convert('L'))
        except Exception as e:
            logger.exception(e)
        else:
            Printer().buffer.image(bc_inverted, impl=cls.impl, center=cls.center)
            logger.debug('Buffering graphics')



     