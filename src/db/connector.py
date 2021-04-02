from tortoise import Tortoise
import os 
from src.db.models import * 
from tortoise import timezone
from src import logger 
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
            modules={'models': ['src.db.models']}
        )
        
        # Generate the schema
        await self.db.generate_schemas()

        # initialize records
        try:
            await Shift.create(id=1)
            await States.create(id=1)
            await Token.create(id=1)
        except Exception as e:
            await logger.error(e)
            pass
        return self

    async def disconnect(self):
        await self.db.close_connections()