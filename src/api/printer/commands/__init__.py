from src.api.printer.commands.document import PrintXML
from src.api.printer.commands.printing import PrintBytes, PrintText
from src.api.printer.commands.querying import ClearBuffer, PrintBuffer, PrinterFullStatusQuery, ModeSetter
from src.api.printer.commands.present import CutPresent


COMMANDS = [PrintXML, PrintBytes, PrintBuffer, PrintText, 
            PrinterFullStatusQuery, PrintBuffer, ClearBuffer, CutPresent]