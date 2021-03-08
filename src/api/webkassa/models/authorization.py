
from pydantic import BaseModel
from pydantic.utils import to_camel
from src.api.webkassa.helpers import to_camel
### REQUEST MODELS ###
class TokenGetRequest(BaseModel):
    login:str
    password:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class TokenGetResponse(BaseModel):
    token:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True

class TokenChangeRequest(BaseModel):
    token:str
    cashbox_unique_number:str
    ofd_token:str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True