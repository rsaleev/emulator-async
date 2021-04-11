from datetime import datetime
from src.api.webkassa.commands import WebkassaClientToken
from src.db.models.token import Token
from src.api.webkassa import logger

class WebkassaClientTokenCheck:
    alias = 'status'

    @classmethod
    async def handle(cls) -> object:
        """
        Method for fetching token from DB
        Returns:
            [object]: returns Pydantic model object created from JSON response
        """
        token_in_db = await Token.filter(id=1).get()
        if token_in_db.token =='' or (token_in_db.ts-datetime.now()).total_seconds()//3600 > 23:
            token = await WebkassaClientToken.handle()
            if token:
                await Token.filter(id=1).update(
                                         token=token,
                                         ts=datetime.now())
            else:
                logger.error("Token not updated")
        
           
            

            
        