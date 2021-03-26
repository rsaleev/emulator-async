
from tortoise.models import Model
from tortoise.fields.data import IntField, CharField, DatetimeField
from datetime import datetime

class Token(Model):
    id = IntField(pk=True)
    token = CharField(max_length=255, default='')
    ts = DatetimeField(auto_now=True, auto_now_add=True) # default value 

    class Meta:
        # dynamically define DB
        table_name = 'token'
