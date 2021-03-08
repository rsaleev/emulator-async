from peewee_async import PooledMySQLDatabase, Manager
from src.db.models import persistent_proxy
from src.db.models.token import Token
from src.db.models.shift import Shift
from src.db.models.receipt import Receipt
from src.db.models.state import States
import os
import asyncio
from playhouse.sqliteq import SqliteQueueDatabase


class MysqlDB:

    def __init__(self):
        self.database = persistent_proxy
        self.loop = asyncio.get_running_loop()
        self.manager = None

    def connect(self):
        """connect [summary]

        [extended_summary]

        Returns:
            [type]: [description]
        """
        database = PooledMySQLDatabase(database=os.getenv('MYSQL_DB'), user=os.getenv('MYSQL_LOGIN'), password=os.getenv('MYSQL_PASSWORD') )
        self.database.initialize(database)
        tables = [Token, Shift, Receipt, States]
        for t in tables:
            t.create_table(True)
        self.manager = Manager(self.database, loop=asyncio.get_running_loop())
        return self.manager

    def disconnect(self):
        self.database.close()
