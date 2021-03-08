from peewee import Model, DateTimeField, IntegerField, UUIDField, FloatField, BooleanField, CharField
from src.db.models import persistent_proxy
from datetime import datetime

class Receipt(Model):
    uid = UUIDField(unique=True)
    ticket = CharField()
    count = IntegerField(default=1)
    price = IntegerField(default=0) 
    payment = IntegerField(default=0)
    tax = FloatField(default=0)
    tax_percent = IntegerField(default=0)
    payment_type = IntegerField(default=1)
    payment_ts = DateTimeField(default=datetime.now)
    sent = BooleanField(default=False)
    ack = BooleanField(default=False)

    class Meta:
        database = persistent_proxy
        table_name = 'receipt'
        primary_key = False