from src.protocols.shtrih.command import ShtrihCommand, ShtrihCommandInterface
import struct


class SubTotal(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x89,))

    @classmethod
    def handle(cls)->bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        arr.extend(bytearray((0x00,0x00,0x00,0x00,0x00)))
        return arr
