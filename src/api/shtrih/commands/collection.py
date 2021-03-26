
import struct
from src.api.shtrih.command import ShtrihCommand


class Withdraw(ShtrihCommand):
   
   
        # count as bytearray element, where B[0] => STX
    _length = bytearray((0x05,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x51,)) #B[2] - 2 byte
    _doc_number = struct.pack('<H',0)
        
    @classmethod
    def handle(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._doc_number)
        return bytes(arr)

class Deposit(ShtrihCommand):

    # count as bytearray element, where B[0] => STX
    _length = bytearray((0x05,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x50,)) #B[2] - 2 byte
    _doc_number = struct.pack('<H',0)
        
    @classmethod
    def handle(cls):
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._doc_number)
        return bytes(arr)




        


