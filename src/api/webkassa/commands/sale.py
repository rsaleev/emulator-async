
import asyncio
from xml.etree.ElementTree import fromstring
from tortoise.expressions import F
from tortoise import timezone
from src import config
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.exceptions import *
from src.api.webkassa.command import WebcassaCommand
from src.db.models import Token, States, Shift
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from src.api.webkassa import logger
from src.api.webkassa.commands import WebkassaClientToken,WebkassaClientCloseShift
from src.api.webkassa.models import SaleRequest, SaleResponse, Position, Payments, CompanyData
from src.api.printer.commands import *

class WebkassaClientSale(WebcassaCommand, WebcassaClient):
    endpoint = 'Check'
    alias = 'sale'

    @classmethod
    async def handle(cls, receipt):
        token = await Token.get(id=1)
        if receipt.price ==0 or receipt.payment ==0: #type: ignore
            logger.error(f'Receipt {receipt.uid} has broken data')#type: ignore 
            raise UnresolvedCommand(f'{cls.alias}: Receipt {receipt.uid} has broken data')
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
            try:    
                receipt.update_from_dict({'sent':True})
                response = await cls.dispatch(endpoint=cls.endpoint, 
                                            request_data=request,   
                                            response_model=SaleResponse, #type: ignore
                                            exc_handler=cls.exc_callback)
                asyncio.ensure_future(receipt.save())
            except Exception as e:
                asyncio.ensure_future(logger.exception(e))
                raise e
            else:
                receipt.update_from_dict({'ack':True})
                await asyncio.gather(receipt.save(),
                                    States.filter(id=1).update(mode=2, gateway=1),
                                    Shift.filter(id=1).update(total_docs=F('total_docs')+1))
                asyncio.create_task(cls._render_receipt(request, response))
                asyncio.ensure_future(receipt.save())


    @classmethod
    async def _render_receipt(cls, request, response):
        """_render_receipt [summary]

        [extended_summary]

        Args:
            request ([type]): [description]
            response ([type]): [description]
        """
        company = CompanyData(name=config['webkassa']['company']['name'],
                            inn=config['webkassa']['company']['inn'])
        template = TEMPLATE_ENVIRONMENT.get_template('receipt.xml')
        render =asyncio.create_task(template.render_async(
            horizontal_delimiter='-',
            dot_delimiter='.',
            whitespace=' ',
            company=company,
            request=request,
            response=response))
        while not render.done():
            await asyncio.sleep(0.02)
        exc = render.exception()
        if exc:
            logger.error(exc)
        else:
            doc = fromstring(render.result())
            asyncio.create_task(cls._print_check(doc))

    @classmethod
    async def _print_check(cls,doc):
        await PrintXML.handle(doc)
        await PrintBuffer.handle()           
        if config['printer']['doc']['ensure_printed']:
            try:
                await asyncio.sleep(config['printer']['doc']['ensure_printed_delay'])
                await CheckLastOperation.handle()
            except:
                asyncio.create_task(EnsurePrintBuffer.handle())
            else:
                await ClearBuffer.handle()
                await CutPresent.handle()
        else:
            await ClearBuffer.handle()
            await CutPresent.handle()

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftExceededTime):
            if config['webkassa']['shift']['autoclose']:
                try:
                    await WebkassaClientCloseShift.handle()
                except:
                    return False
                else:
                    return True
            else:
                # recover from day when no payments were produced and shift wasn't closed on Webkassa service
                shift = await Shift.get(id=1)
                # check if total_docs were 0
                if shift.total_docs ==0:
                    await Shift.filter(id=1).update(open_date=timezone.now(), total_docs=0)
                    return True
                # if docs counter >0 set to mode 3
                else:
                    await States.filter(id=1).update(mode=3)
                    return False
        elif isinstance(exc, ExpiredTokenError):
            try:
                response = await WebkassaClientToken.handle()
                payload.token = response
                return True
            except:
                return False
        elif isinstance(exc, UnrecoverableError):
            return False