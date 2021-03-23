from peewee import State
from src.db.models.state import States


async def check_db():
   states = await States.get_or_none(id=1)
   print(states)
