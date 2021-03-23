from src.api.printer.command import PrinterCommand
from xml.etree.ElementTree import Element
from src import config
import asyncio

class PrintXML(PrinterCommand):


    alias = 'xml'
    CP866 = bytearray((0x17))
    CP1251 = bytearray((0x46))
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

    @classmethod
    async def handle(cls, payload:Element, buffer=True):
        for elem in payload:
            cls._print(elem, buffer)

    @classmethod
    def _print(cls, content:Element, buffer:bool):
        align = content.attrib.get('align', 'left')
        bold = True if content.attrib.get('text', False)  and content.attrib['text']== 'bold' else False
        if content.tag != 'br' and content.attrib.get('text', False): 
            content.text = content.text.replace(u'\u201c','"')
            content.text = content.text.replace(u'\u201d', '"')
            content.text = content.text.replace(u'\u202f', ' ')
            if buffer:
                if config['printer']['doc']['send_encoding']:
                    if cls.encoding_output == 'cp1251':
                        cls.buffer._raw(cls.codepage_command.extend(cls.CP1251)) #type: ignore
                    elif cls.encoding_output == 'cp866':
                        cls.buffer._raw(cls.codepage_command.extend(cls.CP866)) #type: ignore
                cls.buffer.set(align=align, font=cls.font,bold=bold, width=cls.width, height=cls.height, custom_size=cls.custom_size) #type: ignore          
                cls.buffer._raw(content.text.encode(cls.encoding_output))  #type: ignore
            else:
                cls.device._raw(cls.codepage_command) #type: ignore
                cls.device.set(align=align, font=cls.font,bold=bold, width=cls.width, height=cls.height, custom_size=cls.custom_size) #type: ignore          
                cls.device._raw(content.text.encode(cls.encoding_output)) #type: ignore
        elif content.tag == 'br':
            if buffer:
                cls.buffer._raw(bytes("\n", 'ascii')) #type: ignore             
            else:
                cls.device._raw(bytes("\n", 'ascii')) #type: ignore             
                cls.device.set(align=align, font=font, bold=bold, width=1, height=1, custom_size=cls.custom_size) #type: ignore
