from src.db.models import persistent_proxy
from datetime import datetime
from tortoise.models import Model
from tortoise.fields.data import IntField, DatetimeField



class Shift(Model):
    id = IntField(pk=True)
    open_date = DatetimeField(default=datetime.now)
    total_docs = IntField()

    class Meta:
        # dynamically define DB
        database =  persistent_proxy
        table_name = 'shift'
