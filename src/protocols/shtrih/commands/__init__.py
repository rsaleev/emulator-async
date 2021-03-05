from ..commands.collection import Withdraw, Deposit
from ..commands.print import PrintDefaultLine
from ..commands.report import ZReport, XReport
from ..commands.shift import OpenShift, CloseShift
from ..commands.sale import OpenReceipt, OpenSale, SimpleCloseSale
from ..commands.subtotal import SubTotal
from ..commands.state import FullState
from ..commands.table import SerialNumber






COMMANDS =[Withdraw, Deposit, PrintDefaultLine, ZReport, XReport, 
            OpenShift, CloseShift, OpenReceipt, OpenSale, SimpleCloseSale, 
            SubTotal, FullState, SerialNumber]