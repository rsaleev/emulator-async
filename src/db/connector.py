from tortoise import Tortoise
import os 
from src.db.models import *  
from src import logger 
import tzlocal
class DBConnector:

    def __init__(self):
        self.db = Tortoise()
        self.connected = Tortoise._inited
        
    async def connect(self):
        """connect

        initializes Tortoise connection

        Returns:
            [type]: [description]
        """

        await self.db.init(
            db_url=f'sqlite://{os.path.abspath(os.getcwd())}/{os.environ.get("SQLITE_DB")}',
            use_tz=False, 
            timezone = str(tzlocal.get_localzone()),
            modules={'models': ['src.db.models']}
        )
        
        # Generate the schema
        await self.db.generate_schemas()
        # initialize records
        try:
            shift = Shift(id=1)
            await shift.save()
        except Exception as e:
            await logger.error(e)
            pass
        try:
            states = States(id=1)
            await states.save()
        except Exception as e:
            await logger.error(e)
            pass
        try:
            token = Token(id=1)
            await token.create(id=1)
        except Exception as e:
            await logger.error(e)
            pass
        return self

    async def disconnect(self):
        await self.db.close_connections()