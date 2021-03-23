from src.api.webkassa.exceptions import ExpiredTokenError, ShiftAlreadyClosed, CredentialsError, UnrecoverableError
from pydantic import BaseModel
from src.api.webkassa.helpers import to_camel
from typing import Any, Optional, List
from src.db.models.shift import Shift
from src.db.models.token import Token
from src.db.models.state import States
from src import config
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from datetime import datetime
from src.api.webkassa.command import WebcassaCommand, WebcassaGateway
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.commands.authorization import WebkassaClientToken
from src.api.webkassa import logger
from xml.etree.ElementTree import fromstring
import asyncio

""" 
Z/X-REPORT REQUEST

implements both report and state change
"""


class ZXReportRequest(BaseModel):
    token: str
    cashbox_unique_number: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


""" 
Z/X-REPORT RESPONSE
"""


class PaymentByTypesApiModel(BaseModel):
    Sum: Optional[int]
    Type: Optional[int]


class Sell(BaseModel):
    PaymentsByTypesApiModel: Optional[List[PaymentByTypesApiModel]]
    Discount: float
    Markup: float
    Taken: int
    Change: Optional[int] = 0
    Count: int
    VAT: float


class Buy(BaseModel):
    PaymentsByTypesApiModel: Optional[List[PaymentByTypesApiModel]]
    Discount: int
    Markup: int
    Taken: int
    Change: Optional[int] = 0
    Count: int
    VAT: float


class ReturnSell(BaseModel):
    PaymentsByTypesApiModel: Optional[List[PaymentByTypesApiModel]]
    Discount: int
    Markup: int
    Taken: int
    Count: int
    VAT: float


class ReturnBuy(BaseModel):
    PaymentByTypesApiModel: Optional[List[PaymentByTypesApiModel]]
    Discount: int
    Markup: int
    Taken: int
    Count: int
    VAT: float


class EndNonNullable(BaseModel):
    Sell: int
    Buy: int
    ReturnSell: Optional[int]
    ReturnBuy: Optional[int]


class StartNonNullable(BaseModel):
    Sell: int
    Buy: int
    ReturnSell: Optional[int]
    ReturnBuy: Optional[int]


class Ofd(BaseModel):
    Name: str
    Host: str
    Code: int


class ZXReportResponse(BaseModel):
    ReportNumber: int
    TaxPayerName: str
    TaxPayerIN: str
    TaxPayerVAT: bool
    TaxPayerVATSeria: str
    TaxPayerVATNumber: str
    CashboxSN: str
    CashboxIN: str
    CashboxRN: str
    StartOn: str
    ReportOn: str
    CloseOn: str
    CashierCode: int
    ShiftNumber: int
    DocumentCount: int
    PutMoneySum: int
    TakeMoneySum: int
    ControlSum: int
    OfflineMode: bool = False
    CashboxOfflineMode: bool = False
    SumInCashbox: int
    Sell: Optional[Sell]
    Buy: Optional[Buy]
    ReturnSell: Optional[ReturnSell]
    ReturnBuy: Optional[ReturnBuy]
    EndNonNullable: EndNonNullable
    StartNonNullable: StartNonNullable
    Ofd: Ofd


class WebkassaClientZReport(WebcassaCommand, WebcassaClient, WebcassaGateway):

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
                                response_model=ZXReportResponse,
                                callback_error=cls.exc_callback)
            template = TEMPLATE_ENVIRONMENT.get_or_select_template(
                'report.xml')
            name = response.TaxPayerName  #type: ignore
            name.replace(u'\u201c', '"')
            name.replace(u'\u201d', '"')
            rendered = fromstring(template.render(report_type='СМЕННЫЙ Z-ОТЧЕТ',
                                        horizontal_delimiter='-',
                                        response=response,
                                        company_name=name,
                                        tab=' '))
            await Shift.filter(id=1).update(open_date=datetime.now(),
                                    total_docs=0)
            await States.filter(id=1).update(mode=2)
            return rendered
        except Exception as e:
            await logger.exception(e)
            return None

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            await Shift.filter(id=1).update(open_date=datetime.now(),
                                 total_docs=0)
            await States.filter(id=1).update(mode=2)
            return False
        elif isinstance(exc, CredentialsError):
            await States.filter(id=1).update(gateway=0)
            return False
        elif isinstance(exc, UnrecoverableError):
            await States.filter(id=1).update(gateway=0)
            return False
        elif isinstance(exc, ExpiredTokenError):
            await WebkassaClientToken.handle()
            payload.token = await Token.get(id=1)
            return True


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
                                response_model=ZXReportResponse,
                                callback_error=cls.exc_callback)
        
            await Shift.filter(id=1).update(open_date=datetime.now(),
                                 total_docs=0)
            await States.filter(id=1).update(mode=2)
        except Exception as e:
            raise e
       

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            tasks = []
            tasks.append(Shift.filter(id=1).update(open_date=datetime.now(),
                                 total_docs=0))
            tasks.append(States.filter(id=1).update(mode=2))
            await asyncio.gather(*tasks)
            return False
        elif isinstance(exc, CredentialsError):
            await WebkassaClientToken.handle()
            new_token = await Token.get(id=1)
            payload.token = new_token.token 
            return True
        elif isinstance(exc, UnrecoverableError):
            return False

class WebkassaClientXReport(WebcassaCommand, WebcassaClient, WebcassaGateway):

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
                                response_model=ZXReportResponse,
                                callback_error=cls.exc_callback)
        try:
            if config['webkassa']['report']['printable']:
                template = TEMPLATE_ENVIRONMENT.get_or_select_template(
                    'report.xml')
                name = response.TaxPayerName  #type: ignore
                name.replace(u'\u201c', '"')
                name.replace(u'\u201d', '"')
                rendered = fromstring(template.render(report_type='СМЕННЫЙ Х-ОТЧЕТ',
                                        horizontal_delimiter='-',
                                        response=response,
                                        company_name=name,
                                        tab=' '))
                
                return rendered
        except Exception as e:
            raise e

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftAlreadyClosed):
            tasks = []
            tasks.append(Shift.filter(id=1).update(open_date=datetime.now(),
                                 total_docs=0))
            tasks.append(States.filter(id=1).update(mode=2))
            await asyncio.gather(*tasks)
            return False
        elif isinstance(exc, CredentialsError):
            await WebkassaClientToken.handle()
            payload.token = await Token.get(id=1)
            return True
        elif isinstance(exc, UnrecoverableError):
            return False
