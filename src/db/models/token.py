from peewee import CharField, Model, DateTimeField, IntegerField
from src.db.models import persistent_proxy
from datetime import datetime

class Token(Model):
    id = IntegerField(primary_key=True)
    token = CharField()
    ts = DateTimeField(default=datetime.now) # default value 

    class Meta:
        # dynamically define DB
        database = persistent_proxy
        table_name = 'token'
