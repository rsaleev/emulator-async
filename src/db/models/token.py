
from src.db.models import persistent_proxy
from tortoise.models import Model
from tortoise.fields.data import IntField, CharField, DatetimeField
from src.db.models import persistent_proxy
from datetime import datetime

class Token(Model):
    id = IntField(pk=True)
    token = CharField(max_length=255)
    ts = DatetimeField(default=datetime.now) # default value 

    class Meta:
        # dynamically define DB
        database = persistent_proxy
        table_name = 'token'
