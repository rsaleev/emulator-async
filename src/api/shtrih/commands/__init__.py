from ..commands.print import PrintDefaultLine
from ..commands.report import ZReport, XReport
from ..commands.shift import OpenShift, CloseShift
from ..commands.sale import OpenReceipt, OpenSale, SimpleCloseSale
from ..commands.subtotal import SubTotal
from ..commands.state import FullState
from ..commands.table import SerialNumber
from src import logger as root_logger





COMMANDS =[PrintDefaultLine, ZReport, XReport, OpenReceipt, OpenSale, OpenShift, CloseShift, SimpleCloseSale,
            SubTotal, FullState, SerialNumber]