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
        """_send basic method for sending payload to gateway

        Uses aiohttp.ClientSession() 

        Args:
            endpoint (str): endpoint name: e.g. /Check
            payload (dict): data to send, that will be converted to JSON string

        Returns:
            ClientResponse:  returns response as dictionary. Unparsed from JSON with in-built method
        """
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
        """_err_hdlr handler for responses with Errors attribute in payload

        Since current API returns code 200 on every request that was processed successfully,
        an implementation of handler to convert API error code to something meaningful. 
        If API error code presented in payload (attr Errors:[]) callbacks or handlers can be defined 
        for further decision making: continue process or break it immediatly

        Args:
            err (WebcassaOutputErrors): [description]

        Raises:
            UnrecoverableError: Issue that can't be recovered without User interference
            CredentialsError: Issue that can't be recovered without User interference. Check config for credentials
            ExpiredTokenError: Issue recovered automatically: request new token -> send request with new token in payload body
            ShiftExceededTime: Issue can be recovered automatically or if not used autoclose with manually closing Shift
            ReceiptUniqueNumDuplication: Issue has no recovering, just an important information from API to ensure that data was processed

        See API docs for more information about error codes and what they mean
        """
        if err.code in [
                -1, 4, 5, 6, 7, 8, 9, 10, 13, 15, 16, 18, 1014, 505
        ]:
            raise UnrecoverableError(f'Code:{err.code} Msg:{err.text}')
        elif err.code in [1, 3]:
            raise CredentialsError(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 2:
            raise ExpiredTokenError(f'Code:{err.code} Msh:{err.text}')
        elif err.code == 11:
            raise ShiftExceededTime(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 12:
            raise ShiftAlreadyClosed(f'Code:{err.code} Msg:{err.text}')
        elif err.code == 14:
            raise ReceiptUniqueNumDuplication(
                f'Code:{err.code} Msg:{err.text}')

    @classmethod
    async def dispatch(cls, endpoint: str, request_data: BaseModel,
                       response_model:BaseModel, exc_handler: Callable):
        """
        Method for sending requests to Webkassa Service with retrying implementation

        Args:
            endpoint (str): url to send
            request_data (object): request object created from Pydantic model
            response_model (object): Pydantic model for parsing JSON response
            exc_handler (Callable): handler for exceptions that returns boolean value, 
                                    that define to proceed to next iteration or break with exception raised

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
                                        exclude_unset=True)) 
                # assert status code 200 
                asyncio.ensure_future(logger.info(f'Dispatching to Webkassa: {endpoint}'\
                                    f'{request_data.dict(by_alias=True,exclude_unset=True)}')) 
                # convert dict to Pydantic model -> generates object
                output = WebcassaOutput(**response)
                asyncio.ensure_future(logger.info(
                    f'Response from Webkassa:{json.dumps(output.dict(by_alias=True, exclude_unset=True))}'
                )) 
                # check if errors are in payload
                if output.errors:
                    # change status to prevent new requests from Autocash. Show that process was unsuccessful
                    asyncio.ensure_future(States.filter(id=1).update(gateway=0))
                    for err in output.errors:
                        cls._err_hdlr(err)
                else:
                    asyncio.ensure_future(States.filter(id=1).update(gateway=1))
                    return response_model(**output.data)  #type:ignore
            except (ReceiptUniqueNumDuplication,
                    ShiftAlreadyClosed, ShiftExceededTime,ExpiredTokenError) as e:
                # wait until resolver ends pre-processing and return bool: proceed to next attempt or not                
                resolver = await exc_handler(e, request_data)
                if resolver:
                    asyncio.ensure_future(logger.error(
                        f'Catched API error {repr(e)}. Attempt: {counter}. Continue'
                    ))
                    counter += 1
                    continue
                # if resolver return False, then flush warning to log and break process
                else:
                    asyncio.ensure_future(logger.error(
                        f'Max attempts exhausted. Attempt: {counter} Error:{repr(e)}'
                    ))
                    raise e
            except (UnrecoverableError) as e:
                asyncio.ensure_future(logger.error(
                        f'Catched API error {repr(e)}. Attempt: {counter}. Continue'
                    ))
                return 
            except ConnectionError as e:
                # when connection error occures: send request until connection will be established (until attempts will be exhausted)
                counter += 1
                asyncio.ensure_future(logger.error(
                    f'Cacthed connection error. Attempt: {counter} Error:{repr(e)}. Continue'
                ))
                continue
        else:
            # if all attempts were used raise an exception to inform that process was broke.
            raise UnresolvedCommand(
                f'Max attempts exhausted. Attempt: {counter}')
            
