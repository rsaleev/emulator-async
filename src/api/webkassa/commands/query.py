from tortoise import timezone
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
        token_in_db = await Token.filter(id=1).first()
        if token_in_db.token =='' or (token_in_db.ts-timezone.now()).total_seconds()//3600 > 23:
            token = await WebkassaClientToken.handle()
            if token:
                logger.info('Token was updated')
            else:
                logger.error("Token was not updated")
        
           
            

            
        