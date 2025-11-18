from typing import Optional, List, Literal
from ninja import Schema
from typing import List
from decimal import Decimal
from pydantic import BaseModel, AnyUrl, EmailStr


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
    link: Optional[str] = None
    wallet_address: Optional[str] = None
    user_type: UserType

class RegisterUser(UserBase):
    password: str
    profile_image: Optional[str] = None

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

class StudentProfileOut(BaseModel):
    school: str
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    portfolio_url: Optional[AnyUrl] = None

class ProfessionalProfileOut(BaseModel):
    company: str
    title: Optional[str] = None
    linkedin_url: Optional[AnyUrl] = None
    hiring: bool = False
    interests: Optional[str] = None


class ProjectMini(Schema):
    id: int
    title: str

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    # add these with defaults:
    name: Optional[str] = None
    profile_picture: Optional[AnyUrl] = None
    associated_projects: List[str] = []  # or List[ProjectOut] = []
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    link: Optional[AnyUrl] = None
    wallet_address: Optional[str] = None
    user_type: str
    blurb: Optional[str] = None
    is_email_verified: bool = False

    student: Optional[StudentProfileOut] = None
    professional: Optional[ProfessionalProfileOut] = None
    
class AccountSuccessfulResponse(Schema):
    message: str

class UserSearchResult(Schema):
    id: int
    name: str
    email: str

class ProfileImageOut(Schema):
    url: str

class GuestRegisterIn(Schema):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None


class StudentProfileUpdate(Schema):
    school: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    gpa: float | None = None
    portfolio_url: str | None = None


class ProfessionalProfileUpdate(Schema):
    company: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    hiring: bool | None = None
    interests: str | None = None


class UserProfileUpdate(Schema):
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    link: str | None = None
    linkedin: str | None = None
    github: str | None = None

    user_type: str | None = None  # READ ONLY on backend — ignored for safety

    student: StudentProfileUpdate | None = None
    professional: ProfessionalProfileUpdate | None = None