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
    data: Optional[Any] = None
    errors: Optional[List[WebcassaOutputErrors]] = None

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True