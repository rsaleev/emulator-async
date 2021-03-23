from src.api.printer.command import PrinterCommand
from src import config
from src.api.printer import async_logger, sync_logger
import asyncio 


class PrintText(PrinterCommand):

    alias = 'text'
    
    align = 'left'
    font = config['printer']['text']['font']
    heigth = config['printer']['text']['height']
    width = config['printer']['text']['width']
    custom_size = config['printer']['text']['custom_size']
    codepage_command = bytearray((0x1B,0x74))

    
    @classmethod
    async def handle(cls, payload:str, buffer=True):
        loop = asyncio.get_running_loop()
        task = asyncio.create_task(loop.run_in_executor(None, cls._print_text, payload))
        return task

    @classmethod
    def _print_text(cls, payload:str, buffer:bool):
        """
        Method for printing encoded strings
        Assert incoming encoding is 'utf-8'
        Args:
            content (str): simple string with control symbols
            buffer (bool, optional): [description]. Defaults to True.
        """
        if buffer:
            cls.buffer.set(align=cls.align, font=cls.font, bold=False, underline=0, width=1,  #type: ignore
                     height=1, density=9, invert=False, smooth=False, flip=False, double_width=False, double_height=False, 
                    custom_size=False)  #type: ignore
            cls.buffer.text(payload)  #type: ignore
        else:
            cls.device.set(align=cls.align, font=cls.font, bold=False, underline=0, width=1,  #type: ignore
                     height=1, density=9, invert=False, smooth=False, flip=False, double_width=False, double_height=False, 
                    custom_size=False)  #type: ignore
            cls.device.text(payload)  #type: ignore
     

class PrintBytes(PrinterCommand):

    alias = 'bytes'

    codepage_command = bytearray((0x1B,0x74))
    CP866 = bytearray((0x17))
    CP1251 = bytearray((0x46))
    
    encoding_input = config['printer']['text']['input']
    encoding_output = config['printer']['text']['output']
    align = 'left'
    font = config['printer']['text']['font']
    heigth = config['printer']['text']['height']
    width = config['printer']['text']['width']
    custom_size = config['printer']['text']['custom_size']
    double_width = config['printer']['text']['double_width']
    double_heigth = config['printer']['text']['double_height']



    @classmethod
    async def handle(cls, payload:bytearray, buffer=True) -> asyncio.Task:
      
        """
        Method for printing bytes with method _raw()

        Args:
            content (bytearray): array of bytes for output. 
            buffer (bool, optional): [description]. Defaults to True.
        """
        loop = asyncio.get_running_loop()
        task = asyncio.create_task(loop.run_in_executor(None, cls._print_bytes, payload))
        return task


    @classmethod
    def _print_bytes(cls, payload:bytearray, buffer:bool) -> None:
        bits = bin(payload[0])[2:].zfill(8)
        if buffer:
            try:
                cls.buffer.set(align=cls.align, font=cls.font, bold=False, underline=0, width=cls.width,  #type: ignore
                        height=cls.heigth, density=9, invert=False, smooth=False, flip=False, double_width=cls.double_width, double_height=cls.double_heigth, 
                        custom_size=cls.custom_size)  #type: ignore
                if config['printer']['text']['send_encoding']:
                    if cls.encoding_output == 'cp1251':
                        cls.buffer._raw(cls.codepage_command.extend(cls.CP1251)) #type: ignore
                    elif cls.encoding_output == 'cp866':
                        cls.buffer._raw(cls.codepage_command.extend(cls.CP866)) #type: ignore
                content_decoded = payload[1:].decode(cls.encoding_input)
                if bits[6]:
                    content_decoded=f'{content_decoded}\n'
                content_encoded = content_decoded.encode(cls.encoding_output)
                cls.buffer._raw(content_encoded)  #type: ignore
            except Exception as e:
                sync_logger.exception(e)
        else:
            cls.device.set(align=cls.align, font=cls.font, bold=False, underline=0, width=cls.width,  #type: ignore
                     height=cls.heigth, density=9, invert=False, smooth=False, flip=False, double_width=False, double_height=False, 
                    custom_size=cls.custom_size) 
            content_decoded = payload[1:].decode(cls.encoding_input)
            if bits[6]:
                content_decoded=f'{content_decoded}\n'
            content_encoded = content_decoded.encode(cls.encoding_output)
            cls.device._raw(content_encoded)  #type: ignore
