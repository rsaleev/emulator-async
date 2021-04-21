from pydantic import BaseModel
from src.api.webkassa.helpers import to_camel
from typing import Optional, List

""" 
Z/X-REPORT REQUEST

implements both report and state change
"""
class ZXReportRequest(BaseModel):
    token:str
    cashbox_unique_number:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

""" 
Z/X-REPORT RESPONSE
"""
class PaymentByTypesApiModel(BaseModel):
    Sum:Optional[int]
    Type:Optional[int] 

   
class Sell(BaseModel):
    PaymentsByTypesApiModel:Optional[List[PaymentByTypesApiModel]]
    Discount:float
    Markup:float
    Taken:int
    Change:Optional[int]=0
    Count:int
    VAT:float

class Buy(BaseModel):
    PaymentsByTypesApiModel:Optional[List[PaymentByTypesApiModel]]
    Discount:int
    Markup:int
    Taken:int
    Change:Optional[int]=0
    Count:int
    VAT:float

class ReturnSell(BaseModel):
    PaymentsByTypesApiModel:Optional[List[PaymentByTypesApiModel]]
    Discount:int
    Markup:int
    Taken:int
    Count:int
    VAT:float

class ReturnBuy(BaseModel):
    PaymentByTypesApiModel:Optional[List[PaymentByTypesApiModel]]
    Discount:int
    Markup:int
    Taken:int
    Count:int
    VAT:float

class EndNonNullable(BaseModel):
    Sell:int
    Buy:int 
    ReturnSell:Optional[int]
    ReturnBuy:Optional[int] 
   
class StartNonNullable(BaseModel):
    Sell:int
    Buy:int
    ReturnSell:Optional[int]
    ReturnBuy:Optional[int]

class Ofd(BaseModel):
    Name:str
    Host:str
    Code:int

class ZXReportResponse(BaseModel):
    ReportNumber:int
    TaxPayerName:str 
    TaxPayerIN:str
    TaxPayerVAT:bool
    TaxPayerVATSeria:str
    TaxPayerVATNumber:str
    CashboxSN:str
    CashboxIN:str
    CashboxRN:str
    StartOn:str
    ReportOn:str
    CloseOn:Optional[str] 
    CashierCode:int
    ShiftNumber:int
    DocumentCount:int
    PutMoneySum:int
    TakeMoneySum:int
    ControlSum:int
    OfflineMode:bool=False
    CashboxOfflineMode:bool=False
    SumInCashbox:int
    Sell:Optional[Sell]
    Buy:Optional[Buy]
    ReturnSell:Optional[ReturnSell]
    ReturnBuy:Optional[ReturnBuy]
    EndNonNullable:EndNonNullable
    StartNonNullable:StartNonNullable
    Ofd:Ofd

    
