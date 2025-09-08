from typing import Optional
from ninja import Schema
from typing import List


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
    role: str

class AccountSuccessfulResponse(Schema):
    message: str


class ProjectMini(Schema):
    id: int
    title: str

class UserOut(Schema):
    id: int
    name: str
    profile_picture: str
    blurb: Optional[str] = None
    associated_projects: List[ProjectMini]