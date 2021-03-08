from src.utils.logger import CustomLogger
import asyncio
from functools import partial

logger = CustomLogger()


    
async def test_sleep():
    await asyncio.sleep(5)


async def test_log():  
    asyncio.get_running_loop().run_in_executor(None, partial(logger.debug, 'test'))


async def main():
    task1=test_sleep()
    task2=test_log()
    tasks = [task1, task2]
    await asyncio.gather(*tasks)
    

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()




    


