from src.api.printer.device import Printer
from xml.etree.ElementTree import Element
from src import config
import asyncio

class PrintXML(Printer):
    """PrintXML consoledates methods for printing XML document

    """

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
        buffer = config['printer']['doc']['buffer']
        await loop.run_in_executor(None, cls._print_doc, payload, buffer)


    @classmethod
    def _print_doc(cls, payload:Element, buffer:bool):
        """_print_doc private scope method that handles XML document print by iteration over its' elements


        Args:
            payload (Element): XML object
            buffer (bool): perform printing in buffer or bypass. From argument of higher level method
        """
        for elem in payload:
            cls._print_element(elem, buffer)


    @classmethod
    def _print_element(cls, content:Element, buffer:bool):
        """_print_element [summary]

        parses XML object element attributes and values (text) and generates data for printing: font, type and etc.

        Args:
            content (Element): XML object Element
            buffer (bool): perform printing in buffer or bypass. From argument of higher level method
        """
        align = content.attrib.get('align', 'left')
        bold = True if content.attrib.get('text', False)  and content.attrib['text']== 'bold' else False
        if content.tag != 'br' and content.attrib.get('text', False): 
            content.text = content.text.replace(u'\u201c','"')
            content.text = content.text.replace(u'\u201d', '"')
            content.text = content.text.replace(u'\u202f', ' ')
            if buffer:
                if config['printer']['doc']['send_encoding']:
                    if cls.encoding_output == 'cp1251':
                        Printer()._raw(cls.codepage_command.extend(cls.CP1251)) 
                    elif cls.encoding_output == 'cp866':
                        Printer().buffer._raw(cls.codepage_command.extend(cls.CP866)) 
                Printer().buffer.set(align=align, font=cls.font,bold=bold, width=cls.width, height=cls.height, custom_size=cls.custom_size) #type: ignore          
                Printer().buffer._raw(content.text.encode(cls.encoding_output)) 
            else:
                if config['printer']['doc']['send_encoding']:
                    if cls.encoding_output == 'cp1251':
                        Printer()._raw(cls.codepage_command.extend(cls.CP1251))
                    elif cls.encoding_output == 'cp866':
                        Printer()._raw(cls.codepage_command.extend(cls.CP866)) 
                    Printer()._raw(cls.codepage_command) 
                    Printer().set(align=align, font=cls.font,bold=bold, width=cls.width, height=cls.height, custom_size=cls.custom_size) #type: ignore          
                    Printer()._raw(content.text.encode(cls.encoding_output)) 
        elif content.tag == 'br':
            if buffer:
                Printer().buffer._raw(bytes("\n", 'ascii'))             
            else:
                Printer()._raw(bytes("\n", 'ascii'))          
