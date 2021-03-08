
from peewee import Model, DateTimeField, IntegerField
from datetime import datetime
from src.db.models import persistent_proxy



class Shift(Model):
    id = IntegerField(primary_key=True)
    open_date = DateTimeField(default=datetime.now)
    total_docs = IntegerField()

    class Meta:
        # dynamically define DB
        database =  persistent_proxy
        table_name = 'shift'
