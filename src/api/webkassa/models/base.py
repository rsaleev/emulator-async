from src.api.webkassa.helpers import to_camel
from typing import Optional, Any, List
from pydantic import BaseModel

class WebcassaOutputErrors(BaseModel):
    code: int
    text: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class WebcassaOutput(BaseModel):
    """WebcassaOutput 

    Basic response model {'Data':...,} or {'Errors':[...]}

    Response will be converted to object and 
    then concrete model will be used to parse Data into the concrete object concerned to operation

    Args:
        BaseModel ([type]): [description]
    """
    data: Optional[Any] = None
    errors: Optional[List[WebcassaOutputErrors]] = None

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True