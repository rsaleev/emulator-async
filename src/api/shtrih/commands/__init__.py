from functools import WRAPPER_ASSIGNMENTS
from .print import PrintDefaultLine
from .report import ZReport, XReport
from .shift import OpenShift, CloseShift
from .sale import OpenReceipt, OpenSale, SimpleCloseSale
from .subtotal import SubTotal
from .state import FullState
from .table import SerialNumber
from .collection import Deposit, Withdraw




COMMANDS =[PrintDefaultLine, ZReport, XReport, OpenReceipt, OpenSale, OpenShift, CloseShift, SimpleCloseSale,
            SubTotal, FullState, SerialNumber, Deposit, Withdraw]