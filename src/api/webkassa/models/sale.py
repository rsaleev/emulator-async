from decimal import Decimal
from typing import List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, validator
from src.api.webkassa.helpers import to_camel


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
