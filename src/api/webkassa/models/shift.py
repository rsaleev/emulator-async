from pydantic import BaseModel, validator
from dateutil import parser
from src.api.webkassa.helpers import to_camel
from typing import List, Optional

class ShiftHistoryRequest(BaseModel):
    cashbox_unique_number:str
    token:str
    skip:int
    take:int

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class ShiftData(BaseModel):
    shift_number:int
    open_date:str
    close_date:Optional[str] = None

    class Config:

        alias_generator = to_camel
        allow_population_by_field_name = True

    @validator('open_date')
    def open_date_parser(cls, v):
        return parser(v)


    @validator('close_date')
    def close_date_parser(cls, v):
        return parser(v)

class ShiftHistoryResponse(BaseModel):
    cashbox_unique_number:str
    skip:int
    take:int
    total:int
    shifts:Optional[List[ShiftData]]

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
