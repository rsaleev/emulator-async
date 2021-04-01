
from tortoise.models import Model
from tortoise.fields.data import IntField

class States(Model):
    id = IntField(pk=True)
    mode = IntField(default=2)
    submode = IntField(default=1)
    paper = IntField(default=0)
    roll = IntField(default=0)
    cover = IntField(default=0)
    jam = IntField(default=0)
    gateway = IntField(default=0)

    class Meta:
        # dynamically define DB
        table_name = 'states'
