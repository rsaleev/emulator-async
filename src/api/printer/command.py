
   
    
class PrinterCommand:
    device = None
    buffer = None

    @classmethod
    def set_device(cls, arg:object):
        cls.device = arg

    @classmethod
    def set_buffer(cls, arg:object):
        cls.buffer = arg
    

