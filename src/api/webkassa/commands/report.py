import asyncio
from src.api.printer.commands.querying import CheckPrinting
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
from src.api.printer.commands import PrintXML, CutPresent, PrintBuffer

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
                                            exc_handler=cls.exc_handler)
        except Exception as e:
            raise UnresolvedCommand(f'{cls.alias}:{repr(e)}')
        else:
            await asyncio.gather(Shift.filter(id=1).update(open_date=timezone.now(),total_docs=0),
                                    States.filter(id=1).update(mode=2))
            asyncio.create_task(cls._flush_receipts(response.ShiftNumber))
            if config['webkassa']['report']['printable']:
                asyncio.create_task(cls._render_report(request, response))

            
    @classmethod
    async def _render_report(cls, request, response):
        logger.debug('Rendering report')
        template = TEMPLATE_ENVIRONMENT.get_or_select_template(
            'report.xml')
        name = response.TaxPayerName  #type: ignore
        name.replace(u'\u201c', '"')
        name.replace(u'\u201d', '"')
        try:
            render = template.render(report_type='СМЕННЫЙ Z-ОТЧЕТ',
                                horizontal_delimiter='-',
                                response=response,
                                company_name=name,
                                tab=' ')
        except Exception as e:
            logger.exception(e)
        else:
            doc = fromstring(render)
            asyncio.create_task(cls._print_report(doc))

    
    @classmethod
    async def _print_report(cls, doc):
        logger.debug('Printing report')
        await PrintXML.handle(doc)
        await PrintBuffer.handle()
        await CutPresent.handle()
        await CheckPrinting.handle()


    @classmethod
    async def _flush_receipts(cls, shift_number):
        logger.debug('Archiving receipts')
        try:
            receipts = await Receipt.all()
            bulk = []
            for receipt in receipts:
                print(receipt)
                bulk.append(ReceiptArchived(uid=receipt.uid, 
                                            ticket=receipt.ticket, 
                                            count=receipt.count, 
                                            price=receipt.price,
                                            payment=receipt.payment,
                                            payment_ts=receipt.payment_ts,
                                            payment_type=receipt.payment_type,
                                            tax = receipt.tax,
                                            tax_percent=receipt.tax_percent,
                                            ack=receipt.ack,
                                            sent=receipt.sent,
                                            shift_number=shift_number))
            await asyncio.gather(Receipt.all().delete(), ReceiptArchived.bulk_create(bulk))
        except Exception as e:
            logger.exception(e)

    @classmethod
    async def exc_handler(cls, exc, payload):
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
                                          exc_handler=cls.exc_callback)
        except Exception as e:
            raise UnresolvedCommand(f'{cls.alias}:{repr(e)}')
        else:
            shift_task = Shift.filter(id=1).update(
                    open_date=timezone.now(), total_docs=0)
            states_task = States.filter(id=1).update(mode=2)
            await asyncio.gather(shift_task, states_task)
            asyncio.ensure_future(cls._flush_receipts(response.shift_number))

    @classmethod
    async def _flush_receipts(cls, shift_number):
        logger.debug('Printing report reportrchiving receipts')
        try:
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
        except Exception as e:
            logger.exception(e)

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
                                      exc_handler=cls.exc_handler)
        except Exception as e:
            logger.exception(e)
            raise e
        else:
            asyncio.create_task(cls._render_report(request, response))
        
    @classmethod
    async def _render_report(cls, request, response):
        logger.debug('Rendering report')
        template = TEMPLATE_ENVIRONMENT.get_or_select_template(
                    'report.xml')
        name = response.TaxPayerName  #type: ignore
        name.replace(u'\u201c', '"')
        name.replace(u'\u201d', '"')
        try:
            render = template.render(report_type='СМЕННЫЙ Х-ОТЧЕТ',
                                horizontal_delimiter='-',
                                response=response,
                                company_name=name,
                                tab=' ')
        except Exception as e:
            logger.exception(e)
        else:
            doc = fromstring(render)
            print(doc)
            asyncio.create_task(cls._print_report(doc))

    @classmethod
    async def _print_report(cls, doc):        
        logger.debug('Printing report')
        await PrintXML.handle(doc)
        await PrintBuffer.handle()
        await CutPresent.handle()
        await CheckPrinting.handle()

    @classmethod
    async def exc_handler(cls, exc, payload):
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
