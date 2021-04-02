from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.models import TokenGetRequest, TokenGetResponse
from src import config
from src.db.models import Token
from datetime import datetime
from src.api.webkassa.exceptions import CredentialsError, UnrecoverableError
from tortoise import timezone

class WebkassaClientToken(WebcassaClient):
    endpoint = 'Authorize'
    alias = 'token'

    @classmethod
    async def handle(cls) -> object:
        """
        Method for fetching token from Webkassa API
        Returns:
            [object]: returns Pydantic model object created from JSON response
        """
        request = TokenGetRequest(login=config['webkassa']['login'],
                                  password=config['webkassa']['password'])
        response = await WebcassaClient.dispatch(
            endpoint=cls.endpoint,
            request_data=request,
            response_model=TokenGetResponse, #type:ignore
            callback_error=cls.exc_callback)
        if response:
            return response.token
        else:
            return 

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, UnrecoverableError):
            return False
        elif isinstance(exc, CredentialsError):
            return False