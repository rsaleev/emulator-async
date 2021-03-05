from src.protocols.shtrih.command import ShtrihCommand, ShtrihCommandInterface

class OpenSale(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x80,))

    @classmethod
    def handle(cls)->bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls) ->None:
        pass


class OpenReceipt(ShtrihCommand, ShtrihCommandInterface):
    _length = bytearray((0x03,))
    _command_code = bytearray((0x8D,))

    @classmethod
    def handle(cls)->bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._error_code)
        arr.extend(cls._password)
        return arr
    
    @classmethod
    def dispense(cls) ->None:
        pass



class SimpleCloseSale(ShtrihCommand, ShtrihCommandInterface):
    
    _length = bytearray((0x03,))# B[1] LEN - 1 byte
    _command_code = bytearray((0x85,)) #B[2] - 1 byte
    _weblink = bytearray((ord('N'), ord('/'), ord('A')))

    @classmethod
    def handle(cls) -> bytearray:
        arr = bytearray()
        arr.extend(cls._length)
        arr.extend(cls._command_code)
        arr.extend(cls._password)
        arr.extend(cls._weblink)
        return arr

    @classmethod
    def dispense(cls):
        pass
        



    
