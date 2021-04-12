
import aiofiles
import os
import asyncio
from datetime import datetime
from xml.etree.ElementTree import fromstring
import asyncio
from tortoise.expressions import F
from tortoise.functions import Max

from src import config
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.exceptions import *
from src.api.webkassa.command import WebcassaCommand
from src.db.models import Receipt, Token, States, Shift
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from src.api.webkassa import logger
from src.api.webkassa.commands import WebkassaClientToken,WebkassaClientCloseShift
from src.api.webkassa.models import SaleRequest, SaleResponse, Position, Payments, CompanyData
from src.api.printer.commands import PrintXML, CutPresent, PrintQR

class WebkassaClientSale(WebcassaCommand, WebcassaClient):
    endpoint = 'Check'
    alias = 'sale'

    @classmethod
    async def handle(cls, receipt):
        token = await Token.get(id=1)
        if receipt.price ==0 or receipt.payment ==0: #type: ignore
            asyncio.ensure_future(logger.error(f'Receipt {receipt.uid} has broken data'))#type: ignore 
            # if config['emulator']['flush_receipt']:
            #     await cls._flush(receipt) # flush receipt
            return
        else:
            request  = SaleRequest( 
                token=token.token,
                cashbox_unique_number=config['webkassa']['cassa_unique_number'],
                round_type = 2,
                change = receipt.payment-receipt.price, 
                operation_type = 2,
                positions=[Position(
                            count = receipt.count,
                            price = receipt.price, #
                            tax_type =100,
                            tax_percent = receipt.tax_percent, 
                            tax = receipt.tax, 
                            position_name = f"Оплата парковки по билету:{receipt.ticket}")], 
                payments=[Payments(
                            sum= receipt.payment, 
                            payment_type=receipt.payment_type)], 
                external_check_number=str(receipt.uid))     
            request_task = cls.dispatch(endpoint=cls.endpoint, 
                                        request_data=request,   
                                        response_model=SaleResponse, #type: ignore
                                        callback_error=cls.exc_callback)
            record_task = Receipt.filter(id=receipt.id).update(sent=True) 
            response,_ = await asyncio.gather(request_task, record_task)
            if response:
                asyncio.ensure_future(cls._render_receipt(request, response))
            return response 

    @classmethod
    async def _render_receipt(cls, request, response):
        company = CompanyData(name=config['webkassa']['company']['name'],
                            inn=config['webkassa']['company']['inn'])
        template = TEMPLATE_ENVIRONMENT.get_template('receipt.xml')
        try:
            render = await template.render_async(
                horizontal_delimiter='-',
                dot_delimiter='.',
                whitespace=' ',
                company=company,
                request=request,
                response=response)
            doc = fromstring(render)
            task_modify_states = States.filter(id=1).update(gateway=1)
            task_modify_receipt = Receipt.filter(id=receipt.id).update(ack=True) #type: ignore
            task_modify_shift= Shift.filter(id=1).update(total_docs=F('total_docs')+1)
            await asyncio.gather(task_modify_receipt, task_modify_states, task_modify_shift)
        except Exception as e:
            await logger.debug(e)
            return
        else:
            await PrintXML.handle(doc)
            await CutPresent.handle()
        
    @classmethod
    async def exc_callback(cls, exc, payload):
        asyncio.ensure_future(logger.debug(f'Resolving {exc}'))
        await asyncio.sleep(0.2)
        if isinstance(exc, ShiftExceededTime):
            if config['webkassa']['shift']['autoclose']:
                task_shift_close = WebkassaClientCloseShift.handle()
                task_shift_modify = Shift.filter(id=1).update(open_date=datetime.now(),
                                    total_docs=0)
                task_states_modify = States.filter(id=1).update(mode=2)
                await asyncio.gather(task_shift_close, task_shift_modify, task_states_modify)
                return True
            else:
                # recover from day when no payments were produced and shift wasn't closed on Webkassa service
                shift = await Shift.get(id=1)
                # check if total_docs were 0
                if shift.total_docs ==0:
                    await Shift.filter(id=1).update(open_date=datetime.now(),
                                    total_docs=0)
                    return True
                else:
                    await States.filter(id=1).update(mode=4)
                    return False
        elif isinstance(exc, ExpiredTokenError):
            response = await WebkassaClientToken.handle()
            if response:
                payload.token = response
                return True
            else:
                return False
        elif isinstance(exc, UnrecoverableError):
            await States.filter(id=1).update(gateway=0)
            return False
        

    @classmethod
    async def _flush(cls, receipt:Receipt):
        async with aiofiles.open(f'{os.path.abspath(os.getcwd())}/unprocessed_receipts.txt', "a+") as f:
            await f.write(str(receipt))
            await f.flush()
            await Receipt.filter(id=receipt.id).delete()
