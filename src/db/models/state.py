
from peewee import IntegerField, Model
from src.db.models import persistent_proxy


class States(Model):
    id = IntegerField(primary_key=True, unique=True)
    mode = IntegerField(default=2)
    submode = IntegerField(default=1)
    paper = IntegerField(default=1)
    cover = IntegerField(default=0)
    jam = IntegerField(default=0)
    gateway = IntegerField(default=0)

    class Meta:
        # dynamically define DB
        database = persistent_proxy
        table_name = 'states'
