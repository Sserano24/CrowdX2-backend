from typing import Optional
from ninja import Schema

class UserCreateSchema(Schema):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str

class AccountSuccessfulResponse(Schema):
    message: str

# accounts/schemas.py
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


class UserUpdateInput(Schema):
    first_name: str
    last_name: str
    email: str
    bio: Optional[str]
    wallet_address:Optional[str]
    links:Optional[str]
    phone:Optional[str]

