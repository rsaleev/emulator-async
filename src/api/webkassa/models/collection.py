from pydantic import BaseModel
from src.api.webkassa.helpers import to_camel

"""
REQUEST
"""

class MoneyCollectionRequest(BaseModel):
    token:str
    cashbox_unique_number:str
    operation_type:int
    sum:int
    external_check_number:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

"""
RESPONSE
"""

class Ofd(BaseModel):
    name:str
    host:str
    code:int

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
    
class Cashbox(BaseModel):
    unique_number:str
    registration_number:str
    identity_number:str
    address:str
    ofd:Ofd

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class MoneyCollectionResponse(BaseModel):
    offline_mode:bool
    cashbox_offline_mode:bool
    date_time:str
    sum:int
    cashbox:Cashbox

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True