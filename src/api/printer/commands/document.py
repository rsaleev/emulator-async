from urllib.parse import unquote
from src.api.printer.device import Printer
from xml.etree.ElementTree import Element
from src import config
from src.api.printer import logger
from src.db.models import States

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
        await States.filter(id=1).update(submode=5)
        for elem in payload:
            cls._print_element(elem)

    @classmethod
    def _print_element(cls, content:Element):
        """_print_element [summary]

        parses XML object element attributes and values (text) and generates data for printing: font, type and etc.

        Args:
            content (Element): XML object Element
        """
        try:
            align = content.attrib.get('align', 'left')
            bold = True if content.attrib.get('text', False)  and content.attrib['text']== 'bold' else False
            # tag repressented by text attr with value
            if content.tag != 'br' and content.attrib.get('text', False): 
                # escape characters that can't be represented in chosen encoding
                content.text = content.text.replace(u'\u201c','"')
                content.text = content.text.replace(u'\u201d', '"')
                content.text = content.text.replace(u'\u202f', ' ')
                if config['printer']['doc']['send_encoding']:
                    cmd = bytearray()
                    cmd.extend(cls.codepage_command)
                    if cls.encoding_output == 'cp1251':
                        cmd.extend(cls.CP1251)
                    elif cls.encoding_output == 'cp866':
                        cmd.extend(cls.CP866)
                    Printer().buffer._raw(cmd)
                    Printer().buffer.set(align=align, font=cls.font,bold=bold, width=cls.width, height=cls.height, custom_size=cls.custom_size) #type: ignore          
                    output = content.text.encode(cls.encoding_output)
                    Printer().buffer._raw(output) 
            # tag break -> print newline
            elif content.tag == 'br':
                Printer().buffer._raw(bytes("\n", 'ascii'))
            # tag QR code data           
            elif content.tag == 'qr':
                Printer().qr(unquote(str(content.text)))
        except Exception as e:
            logger.exception(e)
            raise e

                    
