from abc import ABC, abstractclassmethod


class AbstractCommand(ABC):
    
    @abstractclassmethod
    async def handle(cls):
        pass

