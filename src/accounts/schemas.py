from typing import Optional, List, Literal
from ninja import Schema
from typing import List
from decimal import Decimal


UserType = Literal["student", "professional"]

class StudentProfileIn(Schema):
    school: str
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[Decimal] = None
    portfolio_url: Optional[str] = None

class ProfessionalProfileIn(Schema):
    company: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    hiring: Optional[bool] = False
    interests: Optional[str] = None  # comma-separated

class UserBase(Schema):
    email: str
    username: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    links: Optional[str] = None
    wallet_address: Optional[str] = None
    user_type: UserType

class RegisterUser(UserBase):
    password: str
    # nested profile data (exactly one required based on user_type)
    student: Optional[StudentProfileIn] = None
    professional: Optional[ProfessionalProfileIn] = None

# For partial updates (PUT/PATCH)
class UserUpdate(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    links: Optional[str] = None
    wallet_address: Optional[str] = None
    blurb: Optional[str] = None

class StudentProfileOut(Schema):
    school: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[Decimal] = None
    portfolio_url: Optional[str] = None

class ProfessionalProfileOut(Schema):
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    hiring: Optional[bool] = None
    interests: Optional[str] = None


class ProjectMini(Schema):
    id: int
    title: str

class UserOut(Schema):
    id: int
    name: str
    profile_picture: str
    blurb: Optional[str] = None
    associated_projects: List[ProjectMini]
    
class AccountSuccessfulResponse(Schema):
    message: str