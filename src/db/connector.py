from tortoise import Tortoise
import os 
from src.db.models import * 
from datetime import datetime

class DBConnector:

    def __init__(self):
        self.db = None
        self.connected = Tortoise._inited
        
    async def connect(self):
        """connect [summary]

        [extended_summary]

        Returns:
            [type]: [description]
        """
        await Tortoise.init(
            db_url=f'sqlite://{os.path.abspath(os.getcwd())}/{os.environ.get("SQLITE_DB")}',
            modules={'models': ['src.db.models']}
        )
        
        # Generate the schema
        await Tortoise.generate_schemas()

        # initialize records
        await Shift.get_or_create(defaults={'open_date':datetime.now()}, id=1)
        await States.get_or_create(id=1)
        await Token.get_or_create(defaults={'token':'', 'ts':datetime.now()})

        self.db = Tortoise._connections
        return self