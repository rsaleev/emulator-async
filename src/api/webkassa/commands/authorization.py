import asyncio
from tortoise import timezone
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.models import TokenGetRequest, TokenGetResponse
from src.api.webkassa import logger
from src import config
from src.db.models import Token
from src.api.webkassa.exceptions import CredentialsError, UnrecoverableError

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
        try:
            response = await WebcassaClient.dispatch(
                endpoint=cls.endpoint,
                request_data=request,
                response_model=TokenGetResponse, #type:ignore
                exc_handler=cls.exc_handler)
        except Exception as e:
            logger.error(e)
            return
        else:
            asyncio.create_task(Token.filter(id=1).update(token=response.token, ts=timezone.now()))
            return response.token

    @classmethod
    async def exc_handler(cls, exc, payload):
        if isinstance(exc, UnrecoverableError):
            return False
        elif isinstance(exc, CredentialsError):
            return False
