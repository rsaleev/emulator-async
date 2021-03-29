from src.api.webkassa.commands import WebkassaClientToken
from src.db.models.token import Token
from datetime import datetime

class WebkassaClientTokenCheck:
    alias = 'status'

    @classmethod
    async def handle(cls) -> object:
        """
        Method for fetching token from DB
        Returns:
            [object]: returns Pydantic model object created from JSON response
        """
        token_in_db = await Token.filter(id=1).get_or_none()
        if token_in_db and token_in_db.token !='':
            if (token_in_db.ts-datetime.now()).total_seconds()//3600 > 23:
                await WebkassaClientToken.handle()
        else:
            await WebkassaClientToken.handle()

            
        