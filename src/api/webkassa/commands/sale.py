
import aiofiles
import os
import asyncio

from xml.etree.ElementTree import fromstring
import asyncio
from tortoise import timezone
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
from src.api.printer.commands import PrintXML, CutPresent

class WebkassaClientSale(WebcassaCommand, WebcassaClient):
    endpoint = 'Check'
    alias = 'sale'

    @classmethod
    async def handle(cls):
        task_receipt_fetch = Receipt.get_or_none(sent=False).annotate(max_value = Max('id'))
        task_token_fetch = Token.get(id=1)
        receipt, token = await asyncio.gather(task_receipt_fetch, task_token_fetch) 
        if receipt.id: #type: ignore
            if receipt.price ==0 or receipt.payment ==0: #type: ignore
                await logger.error(f'Receipt {receipt.uid} has broken data')#type: ignore 
                # if config['emulator']['flush_receipt']:
                #     await cls._flush(receipt) # flush receipt
            else:
                request  = SaleRequest( 
                    token=token.token,
                    cashbox_unique_number=config['webkassa']['cassa_unique_number'],
                    round_type = 2,
                    change = receipt.payment-receipt.price, #type: ignore
                    operation_type = 2,
                    positions=[Position(
                                count = receipt.count, #type: ignore
                                price = receipt.price, #type: ignore
                                tax_type =100,
                                tax_percent = receipt.tax_percent, #type: ignore
                                tax = receipt.tax, #type: ignore
                                position_name = f"Оплата парковки по билету:{receipt.ticket}")], #type: ignore
                    payments=[Payments(
                                sum= receipt.payment, #type: ignore
                                payment_type=receipt.payment_type)], #type: ignore
                    external_check_number=str(receipt.uid))  #type: ignore   
                try:
                    request_task = cls.dispatch(endpoint=cls.endpoint, 
                                            request_data=request,   
                                            response_model=SaleResponse, #type: ignore
                                            callback_error=cls.exc_callback)
                    record_task = Receipt.filter(id=receipt.id).update(sent=True) #type: ignore
                    response,_ = await asyncio.gather(request_task, record_task) 
                except Exception as e:
                    logger.exception(e)
                    raise e
                else:
                    company = CompanyData(name=config['webkassa']['company']['name'],
                                        inn=config['webkassa']['company']['inn'])
                    template = TEMPLATE_ENVIRONMENT.get_template('receipt.xml')
                    rendered = fromstring(template.render(
                        horizontal_delimiter='-',
                        dot_delimiter='.',
                        whitespace=' ',
                        company=company,
                        request=request,
                        response=response))
                    task_state_modify = States.filter(id=1).update(gateway=1)
                    task_receipt_modify = Receipt.filter(id=receipt.id).update(ack=True) #type: ignore
                    task_shift_modify = Shift.filter(id=1).update(total_docs=F('total_docs')+1)
                    task_print = PrintXML.handle(rendered)
                    try:
                        await asyncio.gather(task_state_modify, task_receipt_modify, task_shift_modify, task_print)
                    except Exception as e:
                        await logger.debug(e)
                    await CutPresent.handle()


    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftExceededTime):
            if config['webkassa']['shift']['autoclose']:
                task_shift_close = WebkassaClientCloseShift.handle()
                task_shift_modify = Shift.filter(id=1).update(open_date=timezone.now(),
                                    total_docs=0)
                task_states_modify = States.filter(id=1).update(mode=2)
                await asyncio.gather(task_shift_close, task_shift_modify, task_states_modify)
                return True
            else:
                # recover from day when no payments were produced and shift wasn't closed on Webkassa service
                shift = await Shift.get(id=1)
                # check if total_docs were 0
                if shift.total_docs ==0:
                    await Shift.filter(id=1).update(open_date=timezone.now(),
                                    total_docs=0)
                    return True
                else:
                    await States.filter(id=1).update(mode=4)
                    return False
        elif isinstance(exc, ExpiredTokenError):
            response = await WebkassaClientToken.handle()
            payload.token = response
            return True
        elif isinstance(exc, UnrecoverableError):
            await States.filter(id=1).update(gateway=0)
            return False
        

    @classmethod
    async def _flush(cls, receipt:Receipt):
        async with aiofiles.open(f'{os.path.abspath(os.getcwd())}/unprocessed_receipts.txt', "a+") as f:
            await f.write(str(receipt))
            await f.flush()
            await Receipt.filter(id=receipt.id).delete()
