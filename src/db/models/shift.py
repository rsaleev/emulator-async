from datetime import datetime
from tortoise.models import Model
from tortoise.fields.data import IntField, DatetimeField
from tortoise.timezone import now


class Shift(Model):
    id = IntField(pk=True)
    open_date = DatetimeField(default=now())
    total_docs = IntField(default=0)

    class Meta:
        # dynamically define DB
        table_name = 'shift'
