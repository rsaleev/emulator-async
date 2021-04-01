from tortoise import Tortoise
import os 
from src.db.models import * 
from tortoise import timezone

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
        await Shift.get_or_create(defaults={'open_date':timezone.now()}, id=1)
        await States.get_or_create(id=1)
        await Token.get_or_create(defaults={'token':'', 'ts':timezone.now()})
        
        return self

    async def disconnect(self):
        await self.db.close_connections()