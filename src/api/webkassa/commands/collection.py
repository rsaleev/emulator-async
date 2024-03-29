
from src.api.printer.commands.querying import PrintBuffer, ClearBuffer
from src.api.webkassa.exceptions import * 
from src.db.models import Token, States
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
            response = await cls.dispatch(endpoint=cls.endpoint, 
                                    request_data=request, 
                                    response_model=MoneyCollectionResponse, #type: ignore
                                    exc_handler=cls.exc_handler)
        except Exception as e:
            logger.exception(e)
            raise e 
        else:
            asyncio.create_task(cls._render_collection(request, response))

    @classmethod
    async def _render_collection(cls, request, response):
        logger.debug('Rendering collection report')
        template = TEMPLATE_ENVIRONMENT.get_or_select_template('collection.xml')
        render = asyncio.ensure_future(template.render_async(
            operation_type = request.operation_type,
            request=request,
            response=response))
        while not render.done():
            await asyncio.sleep(0.2)
        exc = render.exception()
        if exc:
            logger.error(exc)
        else:
            doc = fromstring(render.result())
            asyncio.create_task(cls._print_collection(doc))

    @classmethod
    async def _print_collection(cls, doc):
        logger.debug('Printing collection report')
        await PrintXML.handle(doc)
        await PrintBuffer.handle()
        await CutPresent.handle()
        await ClearBuffer.handle()

    @classmethod
    async def exc_handler(cls, exc, payload):
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