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
                response = await cls._send(endpoint=endpoint,
                                                   payload=request_data.dict(
                                                       by_alias=True,
                                                       exclude_unset=True)
                                                   )  
                await logger.debug(
                                    json.dumps(
                                        request_data.dict(by_alias=True,
                                                        exclude_unset=True)))
                await logger.info(f'Dispatching to Webkassa: {endpoint}')
                output = WebcassaOutput(**response)
                task_log_debug_incoming = logger.debug(
                    f'Response from Webkassa:{json.dumps(response)}'
                )  
                if output.errors:
                    task_state_modify_0= States.filter(id=1).update(gateway=0)
                    await asyncio.gather(task_log_debug_incoming, task_state_modify_0)
                    for err in output.errors:
                        cls._err_hdlr(err)
                else:
                    await States.filter(id=1).update(gateway=1)
                    return response_model(**output.data)  #type:ignore
            except (UnrecoverableError, ReceiptUniqueNumDuplication,
                    ShiftAlreadyClosed, ShiftExceededTime) as e:
                # default state on error -> 0
                resolver = await callback_error(e, request_data)
                if resolver:
                    asyncio.ensure_future(logger.error(
                        f'Catched API error {repr(e)}. Attempt: {counter}. Continue'
                    ))
                    counter += 1
                    continue
                else:
                    asyncio.ensure_future(logger.error(
                        f'Max attempts exhausted. Attempt: {counter} Error:{repr(e)}'
                    ))
                    return
            except ConnectionError as e:
                counter += 1
                asyncio.ensure_future(logger.error(
                    f'Cacthed connection error. Attempt: {counter} Error:{repr(e)}. Continue'
                ))
                continue

        else:
            raise UnresolvedCommand(
                f'Max attempts exhausted. Attempt: {counter}')
            
