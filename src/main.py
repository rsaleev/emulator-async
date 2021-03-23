import asyncio
from functools import partial
from datetime import datetime
from src.db.models import * 
from src.db.connector import DBConnector
from src.test_db import check_db



async def main():
    connector = DBConnector()
    await connector.connect()
    await check_db()
    

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()




    


