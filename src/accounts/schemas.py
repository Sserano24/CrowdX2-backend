from typing import Optional
from ninja import Schema

class registerUser(Schema):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str

class loginSchema(Schema):
    email: str
    password: str


class UserSchema(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None 
    bio: Optional[str] = None
    wallet_address: Optional[str] = None  
    links: Optional[str] = None

class AccountSuccessfulResponse(Schema):
    message: str