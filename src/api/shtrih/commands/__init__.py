from src.api.shtrih.commands.print import PrintDefaultLine, Cut
from src.api.shtrih.commands.report import ZReport, XReport
from src.api.shtrih.commands.shift import OpenShift, CloseShift
from src.api.shtrih.commands.sale import OpenReceipt, OpenSale, SimpleCloseSale, AdvancedCloseReceipt
from src.api.shtrih.commands.subtotal import SubTotal
from src.api.shtrih.commands.state import FullState
from src.api.shtrih.commands.table import SerialNumber, TableModify
from src.api.shtrih.commands.collection import Deposit, Withdraw




COMMANDS =[PrintDefaultLine, ZReport, XReport, OpenReceipt, OpenSale, OpenShift, CloseShift, SimpleCloseSale, AdvancedCloseReceipt
            SubTotal, FullState, SerialNumber, Deposit, Withdraw, Cut, TableModify]