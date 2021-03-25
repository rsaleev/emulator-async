from typing import Any, List, Optional
from pydantic import BaseModel
from src import config
from src.api.webkassa import logger
from src.api.webkassa.exceptions import *
from src.db.models.state import States
from .helpers import to_camel
import json
from typing import Callable
from pydantic import BaseModel
import aiohttp

class WebcassaOutputErrors(BaseModel):
    code: int
    text: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class WebcassaOutput(BaseModel):
    data: Optional[Any] = None
    errors: Optional[List[WebcassaOutputErrors]] = None

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class WebcassaClient:

    @classmethod
    async def _send_request(cls, endpoint: str, payload: dict):
        url = config['webkassa']['url']
        timeout = config['webkassa']['timeout']
        headers = {'Content-Type': 'application/json'}
        async with  aiohttp.ClientSession() as session:
            async with session.post(url=f'{url}/{endpoint}',
                            headers=headers,
                            json=payload,
                            timeout=timeout,
                            raise_for_status=True) as response:
                r = await response.json()
                return r 
        
    @classmethod
    def _handle_error(cls, err: WebcassaOutputErrors):
        if err.code in [-1, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 16, 18, 1014, 505]:
            raise UnrecoverableError(f'Code:{err.code} Msg:{err.text}')
        elif err.code in [1, 3]:
            raise CredentialsError(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 2:
            raise ExpiredTokenError(f'Code:{err.code} Msh:{err.text}')
        elif err.code == 11:
            raise ShiftExceededTime(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 14:
            raise ReceiptUniqueNumDuplication(f'Code:{err.code} Msg:{err.text}')

    @classmethod
    async def dispatch(cls, endpoint: str, request_data: object,
                 response_model: object, callback_error: Callable):
        """
        Method for sending requests to Webkassa Service with retrying implementation

        Args:
            endpoint (str): url to send
            request_data (object): request object created from Pydantic model
            response_model (object): Pydantic model for parsing JSON response
            callback_error (Callable): handler for exceptions

        Returns:
            [Union[dict, None]]: if successfull response return object, else returns 
                                    nothing
        """
        counter = 1
        attempts = config['webkassa']['attempts']
        while counter <= attempts:
            try:
                response = await cls._send_request(
                    endpoint=endpoint,
                    payload=request_data.dict(by_alias=True, exclude_unset=True))  #type:ignore
                await logger.debug(json.dumps(request_data.dict(by_alias=True, exclude_unset=True))) #type:ignore
                await logger.info(f'Dispatching to Webkassa: {endpoint}')
                output = WebcassaOutput(**response.json()) #type: ignore 
                logger.debug(f'Response from Webkassa:{json.dumps(response.json())}') #type:ignore
                if output.errors:
                    await States.filter(id=1).update(gateway=0)
                    for err in output.errors:
                        cls._handle_error(err)
                else:
                    await States.filter(id=1).update(gateway=1)
                    return response_model(**output.data) #type:ignore
            except (UnrecoverableError, ReceiptUniqueNumDuplication, ShiftAlreadyClosed, ShiftExceededTime) as e:
                resolver = await callback_error(e,request_data)
                if resolver:
                    await States.filter(id=1).update(gateway=0)
                    logger.error(f'Catched API error {repr(e)}. Attempt: {counter}. Continue')
                    counter+=1
                    continue
                else:
                    await States.filter(id=1).update(gateway=0)
                    await logger.error(f'Max attempts exhausted. Attempt: {counter} Error:{repr(e)}')
                    return None
            except ConnectionError as e:
                await States.filter(id=1).update(gateway=0)
                counter+=1
                await logger.error(f'Cacthed connection error. Attempt: {counter} Error:{repr(e)}. Continue')
                continue
        else:
            await States.filter(id=1).update(gateway=0)
            raise UnresolvedCommand(f'Max attempts exhausted. Attempt: {counter}')
