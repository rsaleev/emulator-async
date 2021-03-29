from src.api.printer.device import Printer   
    
class PrinterCommand(Printer):
    

    def __init__(self):
        super().__init__()


    @classmethod
    def set(cls, **kwargs):
        Printer.set(**kwargs)


    @classmethod
    def qr(cls, **kwargs):
        Printer.qr(**kwargs)


    
   
    

