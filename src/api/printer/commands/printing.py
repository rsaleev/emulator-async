import asyncio 
from urllib.parse import unquote
from xml.etree.ElementTree import Element
from collections import deque
from typing import Union
from src import config
from src.db.models import States
from src.api.printer import logger
from src.api.printer.device import Printer








class PrintBytes(Printer):
    alias = 'bytes'
    codepage_command = bytearray((0x1B,0x74))
    CP866 = bytearray((0x17,))
    CP1251 = bytearray((0x46,))
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
    async def handle(cls, payload:Union[bytes,bytearray]) -> None:
        await States.filter(id=1).update(submode=2)
        try:
            bits = bin(payload[0])[2:].zfill(8)
            Printer().buffer.set(align=cls.align, font=cls.font, bold=False, underline=0, width=cls.width,  
                    height=cls.heigth, density=9, invert=False, smooth=False, flip=False, double_width=cls.double_width, double_height=cls.double_heigth, 
                    custom_size=cls.custom_size)
            if config['printer']['text']['send_encoding']:
                codepage = bytearray()
                codepage.extend(cls.codepage_command)
                if cls.encoding_output == 'CP1251':
                    codepage.extend(cls.CP1251)
                elif cls.encoding_output == 'CP866':
                    codepage.extend(cls.CP866)
                Printer().buffer._raw(codepage)
            content_decoded = payload[1:].decode(cls.encoding_input)
            if bits[6]:
                content_decoded=f'{content_decoded}\n'
            content_encoded = content_decoded.encode(cls.encoding_output)
            Printer().buffer._raw(content_encoded)
        except Exception as e:
            logger.exception(e)
            raise e

class PrintXML(Printer):
    alias = 'xml'
    CP866 = bytearray((0x17,))
    CP1251 = bytearray((0x46,))
    codepage_command = bytearray((0x1B,0x74))
    encoding_input = config['printer']['doc']['input']
    encoding_output = config['printer']['doc']['output']
    align = 'left'
    font = config['printer']['doc']['font']
    height = config['printer']['doc']['height']
    width = config['printer']['doc']['width']
    custom_size = config['printer']['doc']['custom_size']
    double_width = config['printer']['doc']['double_width']
    double_heigth = config['printer']['doc']['double_height']
    buffer = config['printer']['doc']['buffer']

    @classmethod
    async def handle(cls, payload:Element):
        """handle 
        
        Method for handling and processing data to another scope methods

        Method implement asynchronous approach by passing data to synchronous method that will be executed 
        with loop.run_in_executor method for perforing non blockin I/O

        Args:
            payload (Element): XML object - document
            buffer (bool, optional): perform printing in buffer or bypass. Defaults to True.
        """
        loop = asyncio.get_running_loop()
        await States.filter(id=1).update(submode=5)
        await asyncio.sleep(0.1)
        for child in payload:
            await loop.run_in_executor(None, cls._print_element, child)

    @classmethod
    async def _print_element(cls, content:Element):
        """_print_element [summary]

        parses XML object element attributes and values (text) and generates data for printing: font, type and etc.

        Args:
            content (Element): XML object Element
            buffer (bool): perform printing in buffer or bypass. From argument of higher level method
        """
        try:
            align = content.attrib.get('align', 'left')
            bold = True if content.attrib.get('text', False)  and content.attrib['text']== 'bold' else False
            if content.tag != 'br' and content.attrib.get('text', False): 
                content.text = content.text.replace(u'\u201c','"')
                content.text = content.text.replace(u'\u201d', '"')
                content.text = content.text.replace(u'\u202f', ' ')
                if config['printer']['doc']['send_encoding']:
                    cmd = bytearray()
                    cmd.extend(cls.codepage_command)
                    if cls.encoding_output == 'CP1251':
                        cmd.extend(cls.CP1251)
                    elif cls.encoding_output == 'CP866':
                        cmd.extend(cls.CP866)
                    Printer().buffer._raw(cmd)
                Printer().buffer.set(align=align, font=cls.font,bold=bold, width=cls.width, height=cls.height, custom_size=cls.custom_size) #type: ignore          
                output = content.text.encode(cls.encoding_output)
                Printer().buffer._raw(output)
            elif content.tag == 'br':
                Printer().buffer._raw(bytes("\n", 'ascii'))
            elif content.tag == 'qr':
                Printer().buffer.qr(unquote(str(content.text)))
        except Exception as e:
            logger.exception(e)
            raise e


class PrintDeferredBytes(Printer):
    """PrintDeferredBytes 
    
    Storage for deffered printing.

    Args:
        Printer ([type]): [description]
    """
    storage = deque([])

    @classmethod
    async def handle(cls):
        while cls.storage:
            await PrintBytes.handle(cls.storage.popleft())
              
    @classmethod 
    async def append(cls, data:bytes):
        cls.storage.append(bytes)