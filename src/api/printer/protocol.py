
from escpos.printer import Escpos, Dummy
class PrinterProto(Escpos):
    def __init__(self):
        Escpos.__init__(self)
        
    def _raw(self, *args):
        pass
   
    def close(self):
        pass

   