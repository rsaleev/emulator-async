from datetime import datetime
from tortoise.models import Model
from tortoise.fields.data import IntField, DatetimeField
from tortoise import timezone



class Shift(Model):
    id = IntField(pk=True)
    open_date = DatetimeField(default=timezone.now())
    total_docs = IntField(default=0)

    class Meta:
        # dynamically define DB
        table_name = 'shift'
