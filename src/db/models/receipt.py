from src.db.models import persistent_proxy
from datetime import datetime
from tortoise.models import Model
from tortoise.fields.data import UUIDField, CharField, IntField, FloatField, DatetimeField, BooleanField


class Receipt(Model):
    uid = UUIDField(unique=True)
    ticket = CharField(max_length=255)
    count = IntField(default=1)
    price = IntField(default=0) 
    payment = IntField(default=0)
    tax = FloatField(default=0)
    tax_percent = IntField(default=0)
    payment_type = IntField(default=1)
    payment_ts = DatetimeField(default=datetime.now)
    sent = BooleanField(default=False)
    ack = BooleanField(default=False)

    class Meta:
        table = 'receipts'
