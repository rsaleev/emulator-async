import asyncio
from tortoise import timezone
from src.api.webkassa.commands import WebkassaClientToken
from src.db.models import Token
from src.api.watchdogs import logger

class TokenWatchdog:

    def __init__(self):
        self.event = asyncio.Event()        

    async def _token_check(self):
        token_in_db = await Token.filter(id=1).get()
        if token_in_db.token =='' or (token_in_db.ts-timezone.now()).total_seconds()//3600 > 23:
            asyncio.ensure_future(WebkassaClientToken.handle())
        await asyncio.sleep(1)
               
    async def poll(self):
        while not self.event.is_set():
            logger.debug('Checking token')
            await self._token_check()