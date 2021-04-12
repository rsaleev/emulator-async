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

    async def disconnect(self):
        await self.db.close_connections()