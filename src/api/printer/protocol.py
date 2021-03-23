
from escpos.printer import Escpos, Dummy
class PrinterProto(Escpos):
    def __init__(self):
        super().__init__()
        self.buffer = Dummy()
        self.buffer.clear()
    
    def _raw(self, *args):
        pass
   
    def close(self):
        pass