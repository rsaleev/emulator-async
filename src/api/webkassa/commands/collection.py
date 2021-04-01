from src.api.webkassa.exceptions import * 
from src.db.models import Token, Shift, States
from src.api.webkassa.templates import TEMPLATE_ENVIRONMENT
from src.api.webkassa.command import WebcassaCommand
from src.api.webkassa.client import WebcassaClient
from src.api.webkassa.commands import WebkassaClientToken
from src.api.webkassa.models import MoneyCollectionResponse, MoneyCollectionRequest
from xml.etree.ElementTree import fromstring
from src import config
import struct
from uuid import uuid4
from src.api.printer.commands import PrintXML, CutPresent
import asyncio
from src.api.webkassa import logger
from tortoise import timezone


"""

Withdraw/deposit money

"""

class WebkassaClientCollection(WebcassaCommand, WebcassaClient):
    endpoint = 'MoneyOperation'
    alias = 'deposit'

    @classmethod
    async def handle(cls, payload:bytearray, operation_type:int):
        token = await Token.get(id=1)
        request = MoneyCollectionRequest(
            token=token.token,
            cashbox_unique_number=config['webkassa']['cassa_unique_number'],
            operation_type=operation_type,
            sum = struct.unpack('<5B', payload[4:9]),
            external_check_number=str(uuid4()))
        try:
            response = cls.dispatch(endpoint=cls.endpoint, 
                                    request_data=request, 
                                    response_model=MoneyCollectionResponse, #type: ignore
                                    callback_error=cls.exc_callback)
            if response:
                template = TEMPLATE_ENVIRONMENT.get_or_select_template('collection.xml')
                rendered = fromstring(template.render(
                    operation_type = operation_type,
                    request=request,
                    response=response))
                await PrintXML.handle(rendered)
                await CutPresent.handle()
        except Exception as e:
            await logger.exception(e)
            return 

    @classmethod
    async def exc_callback(cls, exc, payload):
        if isinstance(exc, CredentialsError):
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