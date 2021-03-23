from pydantic import BaseModel, ValidationError
from pydantic.utils import to_camel
from src.api.webkassa.helpers import to_camel
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.command import WebcassaGateway
from src import config
from src.db.models.token import Token
from datetime import datetime
from src.api.webkassa.exceptions import CredentialsError, UnrecoverableError
from src.api.webkassa import logger
from src.db.models.token import Token
from src.db.models.state import States

### REQUEST MODELS ###
class TokenGetRequest(BaseModel):
    login:str
    password:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class TokenGetResponse(BaseModel):
    token:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class TokenChangeRequest(BaseModel):
    token:str
    cashbox_unique_number:str
    ofd_token:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class WebkassaClientToken(WebcassaClient, WebcassaGateway):
    endpoint = 'Authorize'
    alias = 'token'

    @classmethod
    async def handle(cls) -> object:
        """
        Method for fetching token from Webkassa API
        Returns:
            [object]: returns Pydantic model object created from JSON response
        """
        request = TokenGetRequest(login=config['webkassa']['login'], password=config['webkassa']['password'])
        response = await WebcassaClient.dispatch(endpoint=cls.endpoint, request_data=request, response_model=TokenGetResponse,callback_error=cls.exc_callback)
        if response:
            await Token.update_or_create(id=1, token=response.token, ts=datetime.now())
    
    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, UnrecoverableError):
            return False
        elif isinstance(exc, CredentialsError):
            return False