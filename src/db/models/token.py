
from tortoise.models import Model
from tortoise.fields.data import IntField, CharField, DatetimeField
from tortoise import timezone
class Token(Model):
    id = IntField(pk=True)
    token = CharField(max_length=255, default='')
    ts = DatetimeField(default=timezone.now(), auto_now=True) # default value 

    class Meta:
        # dynamically define DB
        table_name = 'token'
