# Model UserForAuthenticate
from pydantic import BaseModel


class UserForAuthenticate(BaseModel):
    username: str
    password: str

# Model cho Token


class Token(BaseModel):
    access_token: str
    token_type: str

# Model cho TokenData


class TokenData(BaseModel):
    username: str
    scopes: list[str] = []
