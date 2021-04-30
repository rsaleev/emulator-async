from src.api.printer.commands.printing import PrintBytes, PrintXML, PrintDeferredBytes
from src.api.printer.commands.querying import ClearBuffer, PrintBuffer, PrinterFullStatusQuery, ModeSetter
from src.api.printer.commands.present import CutPresent
from src.api.printer.commands.graphics import PrintGraphicLines, PrintQR


COMMANDS = [PrintXML, PrintBytes, PrintBuffer, 
            PrinterFullStatusQuery, PrintBuffer, ClearBuffer, CutPresent,
            PrintGraphicLines, PrintQR]