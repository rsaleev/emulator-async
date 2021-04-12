import asyncio
from tortoise import timezone
from xml.etree.ElementTree import fromstring

from src import config
from src.db.models import Shift, Token, States, Receipt, ReceiptArchived
from src.api.webkassa.exceptions import ExpiredTokenError, ShiftAlreadyClosed, CredentialsError, UnrecoverableError, UnresolvedCommand
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from src.api.webkassa.command import WebcassaCommand
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.models import ZXReportRequest, ZXReportResponse
from src.api.webkassa.commands.authorization import WebkassaClientToken
from src.api.webkassa import logger
from src.api.printer.commands import PrintXML, CutPresent

class WebkassaClientZReport(WebcassaCommand, WebcassaClient):

    endpoint = 'ZReport'
    alias = 'zreport'

    @classmethod
    async def handle(cls):
        """
        Method for fetching Z-Report data and printout
        """
        token = await Token.filter(id=1).get()
        request = ZXReportRequest(
            token=token.token,
            cashbox_unique_number=config['webkassa']['cassa_unique_number'])
        try:
            response = await cls.dispatch(endpoint=cls.endpoint,
                                            request_data=request,
                                            response_model=ZXReportResponse,#type: ignore
                                            callback_error=cls.exc_callback)
    
            asyncio.create_task(cls._render_report(request, response))
            task_shift_modify = Shift.filter(id=1).update(open_date=timezone.now(),
                                            total_docs=0)
            task_states_modify =  States.filter(id=1).update(mode=2)
            await asyncio.gather(task_shift_modify, task_states_modify)
        except Exception as e:
            raise UnresolvedCommand(f'{cls.alias}:{repr(e)}')
            
    @classmethod
    async def _render_report(cls, request, response):
        await asyncio.sleep(0.1)
        template = TEMPLATE_ENVIRONMENT.get_or_select_template(
            'report.xml')
        name = response.TaxPayerName  #type: ignore
        name.replace(u'\u201c', '"')
        name.replace(u'\u201d', '"')
        try:
            render = await template.render_async(report_type='СМЕННЫЙ Z-ОТЧЕТ',
                                horizontal_delimiter='-',
                                response=response,
                                company_name=name,
                                tab=' ')
            await asyncio.sleep(0.1)
            doc = fromstring(render)
            
            await PrintXML.handle(doc)
            await asyncio.sleep(0.1)
            await CutPresent.handle()
        except Exception as e:
            await logger.exception(e)

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            asyncio.create_task(Shift.filter(id=1).update(open_date=timezone.now(),
                                            total_docs=0))
            asyncio.create_task(States.filter(id=1).update(mode=2))
            return False
        elif isinstance(exc, CredentialsError):
            asyncio.create_task(States.filter(id=1).update(gateway=0))
            return False
        elif isinstance(exc, UnrecoverableError):
            asyncio.create_task(States.filter(id=1).update(gateway=0))
            return False
        elif isinstance(exc, ExpiredTokenError):
            try:
                response = await WebkassaClientToken.handle()
                payload.token = response
                return True
            except:
                return False

class WebkassaClientCloseShift(WebcassaCommand, WebcassaClient):

    endpoint = 'ZReport'
    alias = 'shift'

    @classmethod
    async def handle(cls):
        token = await Token.get(id=1)
        request = ZXReportRequest(
            token=token.token,
            cashbox_unique_number=config['webkassa']['cassa_unique_number'])
        try:
            response = await cls.dispatch(endpoint=cls.endpoint,
                                          request_data=request,
                                          response_model=ZXReportResponse, #type: ignore
                                          callback_error=cls.exc_callback)
            if response:
                shift_task = Shift.filter(id=1).update(
                    open_date=timezone.now(), total_docs=0)
                states_task = States.filter(id=1).update(mode=2)
                await asyncio.gather(shift_task, states_task)
            else:
                await logger.error("Couldn't close shift")
                 
        except Exception as e:
            await logger.exception(e)
            raise e

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            task_shift_modify = Shift.filter(id=1).update(open_date=timezone.now(),
                                          total_docs=0)
            task_states_modify = States.filter(id=1).update(mode=2)
            await asyncio.gather(task_shift_modify, task_states_modify)
            return False
        elif isinstance(exc, CredentialsError):
            try:
                response = await WebkassaClientToken.handle()
                payload.token = response
                return True
            except:
                return False
        elif isinstance(exc, UnrecoverableError):
            return False


class WebkassaClientXReport(WebcassaCommand, WebcassaClient):

    endpoint = 'XReport'
    alias = 'xreport'

    @classmethod
    async def handle(cls):
        """
        Method for fetching X-Report data and printout
        """
        token = await Token.get(id=1)
        request = ZXReportRequest(
            token=token.token,
            cashbox_unique_number=config['webkassa']['cassa_unique_number'])
        try:
            response = await cls.dispatch(endpoint=cls.endpoint,
                                      request_data=request,
                                      response_model=ZXReportResponse, #type: ignore
                                      callback_error=cls.exc_callback)
            if config['webkassa']['report']['printable']:
                template = TEMPLATE_ENVIRONMENT.get_or_select_template(
                    'report.xml')
                name = response.TaxPayerName  #type: ignore
                name.replace(u'\u201c', '"')
                name.replace(u'\u201d', '"')
                render = await template.render_async(report_type='СМЕННЫЙ Х-ОТЧЕТ',
                                    horizontal_delimiter='-',
                                    response=response,
                                    company_name=name,
                                    tab=' ')
                doc = fromstring(render)
                asyncio.create_task(PrintXML.handle(doc)).add_done_callback(CutPresent.handle)
                asyncio.create_task(cls.flush_receipts(response.ShiftNumber))
        except Exception as e:
            asyncio.create_task(logger.exception(e))
            raise e

    @classmethod
    async def flush_receipts(cls, shift_number):
        receipts = await Receipt.all()
        bulk = []
        for receipt in receipts:
            bulk.append(ReceiptArchived(uid=receipt.uid, 
                                        ticket=receipt.ticket, 
                                        count=receipt.count, 
                                        price=receipt.price,
                                        payment=receipt.payment,
                                        payment_ts=receipt.payment_ts,
                                        tax = receipt.tax,
                                        tax_percent=receipt.tax_percent,
                                        ack=receipt.ack,
                                        sent=receipt.sent,
                                        shift_number=shift_number))
        await asyncio.gather(Receipt.all().delete(), ReceiptArchived.bulk_create(bulk))

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, CredentialsError):
            return False
        elif isinstance(exc, UnrecoverableError):
            return False
        elif isinstance(exc, ExpiredTokenError):
            try:
                response = await WebkassaClientToken.handle()
                payload.token = response
                return True
            except:
                return False
