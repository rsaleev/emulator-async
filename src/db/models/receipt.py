from tortoise.models import Model
from tortoise.fields.data import UUIDField, CharField, IntField, FloatField, DatetimeField, BooleanField, BigIntField
from tortoise import timezone

class Receipt(Model):
    id = IntField(pk=True)
    uid = UUIDField(unique=True)
    ticket = CharField(default='', max_length=255)
    count = IntField(default=1)
    price = IntField(default=0) 
    payment = IntField(default=0)
    tax = FloatField(default=0)
    tax_percent = IntField(default=0)
    payment_type = IntField(default=1)
    payment_ts = DatetimeField(auto_now=True)
    sent = BooleanField(default=False)
    ack = BooleanField(default=False)

    def __str__(self):
        msg =  f"ID:{self.id} UID:{self.uid} "\
                f"TICKET:{self.ticket} COUNT:{self.count} "\
                f"PRICE: {self.price} PAYMENT:{self.payment} "\
                f"TAX: {self.tax} TAX_PERCENT:{self.tax_percent} "\
                f"PAYMENT_TYPE: {self.payment_type} PAYMENT TS: {self.payment_ts}" 
        return msg

    class Meta:
        table = 'receipts'
        ordering = ["id"]


class ReceiptArchived(Model):
    id = IntField(pk=True)
    uid = UUIDField(unique=True)
    ticket = CharField(max_length=255)
    count = IntField(default=1)
    price = IntField(default=0) 
    payment = IntField(default=0)
    tax = FloatField(default=0)
    tax_percent = IntField(default=0)
    payment_type = IntField(default=1)
    payment_ts = DatetimeField(auto_now=True)
    sent = BooleanField(default=False)
    ack = BooleanField(default=False)
    shift_num = IntField(default=0)


    def __str__(self):
        msg =  f"ID:{self.id} UID:{self.uid} "\
                f"TICKET:{self.ticket} COUNT:{self.count} "\
                f"PRICE: {self.price} PAYMENT:{self.payment} "\
                f"TAX: {self.tax} TAX_PERCENT:{self.tax_percent} "\
                f"PAYMENT_TYPE: {self.payment_type} PAYMENT TS: {self.payment_ts}"  
        return msg

    class Meta:
        table = 'receipts_archived'
        ordering = ["id"]