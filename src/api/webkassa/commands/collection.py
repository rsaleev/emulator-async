from pydantic import BaseModel
from src.api.webkassa.exceptions import * 
from src.db.models.token import Token
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from src.api.webkassa.command import WebcassaCommand
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.commands.authorization import WebkassaClientToken
from src import config

"""

Withdraw/deposit money

"""


"""
REQUEST
"""

class MoneyCollectionRequest(BaseModel):
    token:str
    cashbox_unique_number:str
    operation_type:int
    sum:int
    external_check_number:str

"""
RESPONSE
"""

class Ofd(BaseModel):
    name:str
    host:str
    code:int
    
class Cashbox(BaseModel):
    unique_number:str
    registration_number:str
    identity_number:str
    address:str
    ofd:Ofd

class MoneyCollectionResponse(BaseModel):
    offline_mode:bool
    cashbox_offline_mode:bool
    date_time:str
    sum:int
    cashbox:Cashbox


class WebkassaClientCollection:
    endpoint = 'MoneyOperation'
    alias = 'deposit'

    @classmethod
    def handle(cls, payload:bytearray):
        # request = MoneyCollectionRequest(
        #     token=Token.get(),
        #     cashbox_unique_number=config['webkassa']['cassa_unique_number'],
        #     operation_type=operation_type,
        #     sum = struct.unpack('<5B', payload[4:9]),
        #     external_check_number=str(uuid4()))
        # response = self.dispatch(endpoint=endpoint, request_data=request, response_model=MoneyCollectionResponse, callback_error=self.exc_callback)
        # if response:
        #     template = TEMPLATE_ENVIRONMENT.get_or_select_template('collection.xml')
        #     rendered = template.render(
        #         operation_type = operation_type,
        #         request=request,
        #         response=response)
        #     rendered_doc = fromstring(rendered)
        #     return rendered
        pass
