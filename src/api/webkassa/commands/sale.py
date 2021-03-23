from decimal import Decimal
from src.api.webkassa.client import WebcassaClient
from typing import List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel
from src import config
from src.api.webkassa.exceptions import *
from src.api.webkassa.helpers import to_camel
from src.api.webkassa.command import WebcassaCommand, WebcassaGateway
from src.db.models.receipt import Receipt
from src.db.models.token import Token
from src.db.models.state import States
from src.db.models.shift import Shift
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from src.api.webkassa import logger
from src.api.webkassa.commands.authorization import WebkassaClientToken
from src.api.webkassa.commands.report import WebkassaClientCloseShift
from datetime import datetime
from xml.etree.ElementTree import fromstring
import asyncio


from pydantic import BaseModel


class CompanyData(BaseModel):
    inn:str
    name:str

""" 
SALE REQUEST 

Webcassa 2.0
"""
class Position(BaseModel):
        count:Union[int, Decimal]
        price:Union[int, Decimal]
        tax_percent:int=0
        tax:float=0
        tax_type:int=1
        position_name:str
        position_code:Optional[str] = None
        discount:Optional[int] = None 
        markup:Optional[int] = None
        section_code:Optional[str] = None
        is_storno:Optional[bool] = None
        markup_deleted:Optional[bool] = None
        unit_code:int = 1
        mark:Optional[str] = None
            
        class Config:
            alias_generator = to_camel
            allow_population_by_field_name = True


class TicketModifier(BaseModel):
    sum:int
    text:int
    type:int
    tax_type:int
    tax:float

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class Payments(BaseModel):
    sum:int
    payment_type:int = 0

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

### MAIN MODEL ###

### Inherited models above ###

class SaleRequest(BaseModel):
    token:str
    cashbox_unique_number:str
    operation_type:int
    positions:List[Position]
    ticket_modifiers:Optional[List[TicketModifier]]
    payments:List[Payments]
    change:Optional[int] = None 
    round_type:int
    external_check_number:str = str(uuid4())
    customer_email:Optional[str] = None

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
    
""" 
SALE RESPONSE

Webcassa 2.0
"""

class OfdData(BaseModel):
    name:str
    host:str
    code:int 

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class CashboxData(BaseModel):
    unique_number:str
    registration_number:str
    identity_number:str
    address:str
    ofd: OfdData

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class SaleResponse(BaseModel):
    check_number:str
    date_time:str
    offline_mode:bool
    cashbox_offline_mode: bool
    cashbox:CashboxData
    check_order_number:int
    shift_number:int
    employee_name:str
    ticket_url:str 
    ticket_print_url:Optional[str]  

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class WebkassaClientSale(WebcassaCommand, WebcassaGateway, WebcassaClient):
    endpoint = 'Check'
    alias = 'sale'

    @classmethod
    async def handle(cls):
        tasks = [Receipt.get(), Token.get(id=1)]
        receipt, token = await asyncio.gather(*tasks) #type:ignore
        await logger.debug(receipt)
        if receipt.price ==0 or receipt.payment ==0:
           await logger.error(f'Receipt {receipt.uid} has broken data')
        else:
            request  = SaleRequest(
                token=token.token,
                cashbox_unique_number=config['webkassa']['cassa_unique_number'],
                round_type = 2,
                change = receipt.payment-receipt.price,
                operation_type = 2,
                positions=[Position(
                            count = receipt.count,
                            price = receipt.price,
                            tax_type =100,
                            tax_percent = receipt.tax_percent,
                            tax = receipt.tax,
                            position_name = f"Оплата парковки по билету:{receipt.ticket}")],
                payments=[Payments(
                            sum= receipt.payment,
                            payment_type=receipt.payment_type)],
                external_check_number=str(receipt.uid))     
            try:
                response = cls.dispatch(endpoint=cls.endpoint, request_data=request, response_model=SaleResponse,callback_error=cls.exc_callback)
                company = CompanyData(name=config['webkassa']['company']['name'], inn=config['webkassa']['company']['inn'])
                template = TEMPLATE_ENVIRONMENT.get_template('receipt.xml')
                rendered = fromstring(template.render(
                    horizontal_delimiter='-',
                    dot_delimiter='.',
                    whitespace=' ',
                    company=company,
                    request=request,
                    response=response))
                tasks = []
                tasks.append(States.filter(id=1).update(gateway=1))
                tasks.append(Receipt.filter(uid=receipt.uid).delete())
                tasks.append(Shift.filter(id=1).update(total_docs=Shift.total_docs+1))
                await asyncio.gather(*tasks)
                return rendered
            except Exception as e:
                logger.exception(e)

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, ShiftExceededTime):
            if config['webkassa']['shift']['autoclose']:
                tasks = []
                tasks.append(WebkassaClientCloseShift.handle())
                tasks.append(Shift.filter(id=1).update(open_date=datetime.now(),
                                    total_docs=0))
                tasks.append(States.filter(id=1).update(mode=2))
                await asyncio.gather(*tasks)
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
            await WebkassaClientToken.handle()
            payload.token = Token.get()
            return True
        elif isinstance(exc, UnrecoverableError):
            await States.filter(id=1).update(gateway=0)
            return False
            