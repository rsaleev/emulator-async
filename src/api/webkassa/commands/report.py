from src.api.webkassa.exceptions import ExpiredTokenError, ShiftAlreadyClosed, CredentialsError, UnrecoverableError
from src.db.models import Shift, Token, States
from src import config
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from datetime import datetime
from src.api.webkassa.command import WebcassaCommand
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.models import ZXReportRequest, ZXReportResponse
from src.api.webkassa.commands.authorization import WebkassaClientToken
from src.api.webkassa import logger
from xml.etree.ElementTree import fromstring
import asyncio
from tortoise import timezone
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
            template = TEMPLATE_ENVIRONMENT.get_or_select_template(
                'report.xml')
            name = response.TaxPayerName  #type: ignore
            name.replace(u'\u201c', '"')
            name.replace(u'\u201d', '"')
            rendered = fromstring(
                template.render(report_type='СМЕННЫЙ Z-ОТЧЕТ',
                                horizontal_delimiter='-',
                                response=response,
                                company_name=name,
                                tab=' '))
                
            task_shift_modify = Shift.filter(id=1).update(open_date=timezone.now(),
                                            total_docs=0)
            task_states_modify =  States.filter(id=1).update(mode=2)
            tasks_print_xml = PrintXML.handle(rendered, buffer=False)
            await asyncio.gather(task_shift_modify, task_states_modify, tasks_print_xml)
            await CutPresent.handle()
        except Exception as e:
            await logger.exception(e)
            return 

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            task_shift_modify = Shift.filter(id=1).update(open_date=timezone.now(),
                                            total_docs=0)
            task_states_modify=  States.filter(id=1).update(mode=2)
            await asyncio.gather(task_shift_modify, task_states_modify)
            return False
        elif isinstance(exc, CredentialsError):
            await States.filter(id=1).update(gateway=0)
            return False
        elif isinstance(exc, UnrecoverableError):
            await States.filter(id=1).update(gateway=0)
            return False
        elif isinstance(exc, ExpiredTokenError):
            response = await WebkassaClientToken.handle()
            if response:
                payload.token = response
                return True
            else:
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

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            task_shift_modify = Shift.filter(id=1).update(open_date=timezone.now(),
                                          total_docs=0)
            task_states_modify = States.filter(id=1).update(mode=2)
            await asyncio.gather(task_shift_modify, task_states_modify)
            return False
        elif isinstance(exc, CredentialsError):
            response = await WebkassaClientToken.handle()
            if response:
                payload.token = response
                return True
            else:
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
        response = await cls.dispatch(endpoint=cls.endpoint,
                                      request_data=request,
                                      response_model=ZXReportResponse, #type: ignore
                                      callback_error=cls.exc_callback)
        try:
            if config['webkassa']['report']['printable']:
                template = TEMPLATE_ENVIRONMENT.get_or_select_template(
                    'report.xml')
                name = response.TaxPayerName  #type: ignore
                name.replace(u'\u201c', '"')
                name.replace(u'\u201d', '"')
                rendered = fromstring(
                    template.render(report_type='СМЕННЫЙ Х-ОТЧЕТ',
                                    horizontal_delimiter='-',
                                    response=response,
                                    company_name=name,
                                    tab=' '))

                await PrintXML.handle(rendered)
                await CutPresent.handle()
        except Exception as e:
            await logger.exception(e)

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, CredentialsError):
            return False
        elif isinstance(exc, UnrecoverableError):
            return False
        elif isinstance(exc, ExpiredTokenError):
            response = await WebkassaClientToken.handle()
            if response:
                payload.token = response
                return True
            else:
                return False
