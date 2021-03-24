
from tortoise.models import Model
from tortoise.fields.data import IntField, CharField, DatetimeField
from datetime import datetime

class Token(Model):
    id = IntField(pk=True)
    token = CharField(max_length=255)
    ts = DatetimeField(default=datetime.now) # default value 

    class Meta:
        # dynamically define DB
        table_name = 'token'
