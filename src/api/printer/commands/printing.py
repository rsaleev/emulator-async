from src.api.printer.command import PrinterCommand
from src.api.printer.device import PrinterProxyDevice
from typing import Union, List
from asyncio import Task
from xml.etree.ElementTree import Element as XMLElement


class PrintBytes(PrinterCommand):
    _command_alias = 'print_bytes'

    @classmethod
    async def handle(cls, payload:Union[bytes, bytearray], callback) -> Union[Task, None]: 
        payload = payload.decode('cp1251').encode('cp866')
        callback(payload)

class PrintXML(PrinterCommand):
    _command_code = 'print_xml'

    @classmethod
    async def handle(cls, payload:XMLElement, callback) -> Union[Task, None]:
        payload.text.replace(u'\u201c','"')
        payload.text.replace(u'\u201d', '"')
        payload.text.replace(u'\u202f', ' ')
        callback(bytes(payload.text, 'cp866')) #type: ignore

class PrintQR(PrinterCommand):
    _command_code = 'print_qr'


class PrintBuffer(PrinterCommand):
    _command_code = 'print_buffer'

    @classmethod
    async def handle(cls):
        task = device.write(device.buffer.output) #type: ignore
        return task

class Cut(PrinterCommand):

    _command_code ='cut'

    @classmethod
    async def handle(cls):
        pass






