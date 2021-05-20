from src.api.shtrih.commands.print import PrintDefaultLine, Cut, PrintOneDimensionalBarcode
from src.api.shtrih.commands.report import ZReport, XReport
from src.api.shtrih.commands.shift import OpenShift, CloseShift
from src.api.shtrih.commands.sale import CancelReceipt, OpenReceipt, OpenSale, SimpleCloseSale, OpenSale2, CloseReceipt2
from src.api.shtrih.commands.subtotal import SubTotal
from src.api.shtrih.commands.state import FullState
from src.api.shtrih.commands.table import SerialNumber, TableModify
from src.api.shtrih.commands.collection import Deposit, Withdraw



COMMANDS =[PrintDefaultLine, Cut, PrintOneDimensionalBarcode,
            ZReport, XReport, 
            OpenReceipt, OpenSale, SimpleCloseSale,OpenSale2, CloseReceipt2,SubTotal, CancelReceipt,
            OpenShift, CloseShift, 
            FullState, SerialNumber, Deposit, Withdraw, TableModify]
