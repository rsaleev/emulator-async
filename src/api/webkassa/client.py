from src import config
from src.api.webkassa import logger
from src.api.webkassa.exceptions import *
from src.api.webkassa.models import WebcassaOutput, WebcassaOutputErrors
from src.db.models import States
import json
from typing import Callable
import aiohttp
from pydantic import BaseModel
import asyncio


class WebcassaClient:

    url = config['webkassa']['url']
    timeout = config['webkassa']['timeout']
    headers = {'Content-Type': 'application/json'}

    @classmethod
    async def _send(cls, endpoint: str, payload: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f'{cls.url}/{endpoint}',
                                    headers=cls.headers,
                                    json=payload,
                                    timeout=cls.timeout,
                                    raise_for_status=True) as response:
                r = await response.json()
                return r

    @classmethod
    def _err_hdlr(cls, err: WebcassaOutputErrors):
        if err.code in [
                -1, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 16, 18, 1014, 505
        ]:
            raise UnrecoverableError(f'Code:{err.code} Msg:{err.text}')
        elif err.code in [1, 3]:
            raise CredentialsError(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 2:
            raise ExpiredTokenError(f'Code:{err.code} Msh:{err.text}')
        elif err.code == 11:
            raise ShiftExceededTime(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 14:
            raise ReceiptUniqueNumDuplication(
                f'Code:{err.code} Msg:{err.text}')

    @classmethod
    async def dispatch(cls, endpoint: str, request_data: BaseModel,
                       response_model:BaseModel, callback_error: Callable):
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
                await logger.info(f'Dispatching to Webkassa: {endpoint}'\
                                    f'{request_data.dict(by_alias=True,exclude_unset=True)}')
                response = await cls._send(endpoint=endpoint,
                                        payload=request_data.dict(
                                        by_alias=True,
                                        exclude_unset=True))  
                asyncio.create_task(logger.info(
                    f'Response from Webkassa:{json.dumps(response)}'
                )) 
                output = WebcassaOutput(**response)
                
                if output.errors:
                    asyncio.create_task(States.filter(id=1).update(gateway=0))
                    for err in output.errors:
                        cls._err_hdlr(err)
                else:
                    asyncio.create_task(States.filter(id=1).update(gateway=1))
                    return response_model(**output.data)  #type:ignore
            except (ReceiptUniqueNumDuplication,
                    ShiftAlreadyClosed, ShiftExceededTime,ExpiredTokenError) as e:
                # default state on error -> 0
                resolver = await callback_error(e, request_data)
                if resolver:
                    asyncio.create_task(logger.error(
                        f'Catched API error {repr(e)}. Attempt: {counter}. Continue'
                    ))
                    counter += 1
                    continue
                else:
                    asyncio.create_task(logger.error(
                        f'Max attempts exhausted. Attempt: {counter} Error:{repr(e)}'
                    ))
                    return
            except (UnrecoverableError) as e:
                asyncio.create_task(logger.error(
                        f'Catched API error {repr(e)}. Attempt: {counter}. Continue'
                    ))
                return 
            except ConnectionError as e:
                counter += 1
                await States.filter(id=1).update(gateway=0)
                asyncio.create_task(logger.error(
                    f'Cacthed connection error. Attempt: {counter} Error:{repr(e)}. Continue'
                ))
                continue
        else:
            raise UnresolvedCommand(
                f'Max attempts exhausted. Attempt: {counter}')
            
