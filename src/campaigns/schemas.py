from datetime import datetime
from decimal import Decimal
from ninja import Schema
from typing import List, Optional
from datetime import date
from .models import Campaign
from pydantic import EmailStr, BaseModel



# Schema for creating a new campaign entry (user is taken from request.user)
class CampaignEntryCreateSchema(Schema):
    title: str
    description: str
    goal_amount: Decimal
    start_date: datetime
    end_date: datetime | None = None

#from accounts.schemas import UserSchema  # import your user schema

class CampaignEntryDetailSchema(Schema):
    id: int
    title: str
    description: str
    goal_amount: Decimal
    current_amount: Decimal
    start_date: datetime
    end_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
    #creator: UserSchema  # ✅ link to user

class CampaignEntryListSchema(Schema):
    id: int
    title: str
    description: str
    goal_amount: Decimal
    current_amount: Decimal
    start_date: datetime
    end_date: datetime | None = None
    #creator: UserSchema  # ✅ optional but useful

class CampaignEntryCreateSchema(Schema):
    title: str
    description: str
    school: Optional[str] = None
    tags: Optional[str] = None
    sponsored_by: Optional[str] = None
    goal_amount: Decimal
    end_date: Optional[str] = None   # YYYY-MM-DD
    milestones: Optional[List[dict]] = None
    team_members: Optional[List[int]] = None
    
class UserWithCampaignsSchema(Schema):
    id: int
    username: str
    campaigns: List[CampaignEntryListSchema]


class CampaignOut(Schema):
    id: int
    title: str
    description: str
    goal_amount: float
    current_amount: float
    created_at: datetime
    updated_at: datetime
    creator_id: int  # ✅ explicitly include the FK as an integer


class StatsOut(Schema):
    active_projects: int
    active_creators: int
    funds_raised: int

class UserOut(Schema):
    id: int
    email: str
    associated_projects: List[int]
    user_score: int


# class CampaignOut(Schema):
#     id: int
#     title: str
#     description: str
#     school: Optional[str]
#     current_amount: int
#     goal_amount: int
#     tags: List[str]
#     cover_image: Optional[str]    
#     backers: int         

class SearchResponse(Schema):
    items: List[CampaignOut]
    total: int
    page: int
    page_size: int

class SecretResponse(Schema):
    account_id: str
    client_secret: str
    created: bool  # whether we created a new Stripe account this call


# ---------- Schemas ----------
class MilestoneIn(Schema):
    title: str
    done: bool = False


class CampaignIn(Schema):
    title: str
    description: str
    goal_amount: Decimal
    creator_id: int

    # optional
    school: Optional[str] = None
    tags: List[str] = []                 # we’ll join to a comma string
    team_member_ids: List[int] = []      # AUTH_USER_MODEL ids
    end_date: Optional[date] = None
    milestones: Optional[List[MilestoneIn]] = None


class CampaignOut(Schema):
    id: int
    title: str
    description: str
    school: Optional[str]
    tags: List[str]                      # split back to list for convenience
    goal_amount: Decimal
    current_amount: Decimal
    creator_id: int
    team_member_ids: List[int]
    is_active: bool
    start_date: date
    end_date: Optional[date]

    @classmethod
    def from_model(cls, c: Campaign):
        return cls(
            id=c.id,
            title=c.title,
            description=c.description,
            school=c.school,
            tags=[t.strip() for t in (c.tags or "").split(",") if t.strip()],
            goal_amount=c.goal_amount,
            current_amount=c.current_amount,
            creator_id=c.creator_id,
            team_member_ids=list(c.team_members.values_list("id", flat=True)),
            is_active=c.is_active,
            start_date=c.start_date,
            end_date=c.end_date,
        )

from datetime import date
from typing import List, Optional
from ninja import Schema


class CreatorSchema(BaseModel):
    id: int
    name: str
    avatar: Optional[str]
    major: Optional[str]
    school: Optional[str]
    bio: str
    linkedin:str


class TeamMemberSchema(Schema):
    id: int
    name: str
    role: str
    bio: str
    linkedin: Optional[str] = None


class MilestoneSchema(Schema):
    title: str
    details: str
    status: bool
    


class ContactSchema(Schema):
    email: str
    github: Optional[str] = None
    youtube: Optional[str] = None

class CampaignImageSchema(Schema):
    id: int
    url: str
    caption: str = ""


class CampaignSchema(Schema):
    id: int
    title: str
    like_count: int
    liked: bool | None = None 
    school: Optional[str] = None
    one_line: str
    project_summary: str
    is_creator_viewing: bool  # 👈 ADD THIS

    problem_statement: str
    proposed_solution: str
    technical_approach: str
    implementation_progress: str
    impact_and_future_work: str
    mentorship_or_support_needs: str

    goal_amount: int
    current_amount: int

    tags: List[str]
    images: list[CampaignImageSchema] = []

    creator: CreatorSchema
    team_members: List[TeamMemberSchema]

    is_sponsored: bool
    sponsored_by: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    milestones: List[MilestoneSchema]

    verified: bool
    contact: ContactSchema

class TeamMemberIn(Schema):
    id: int
    role: str = ""


class MilestoneIn(Schema):
    title: str
    status: bool
    details: str = ""
    milestone_goal: Decimal


class ContactIn(Schema):
    email: Optional[EmailStr] = None
    github: Optional[str] = None
    youtube: Optional[str] = None


class CampaignCreateSchema(Schema):
    title: str
    one_line: str
    project_summary: str
    problem_statement: str
    proposed_solution: str
    technical_approach: str
    implementation_progress: str
    impact_and_future_work: str
    mentorship_or_support_needs: str

    goal_amount: Decimal
    fiat_funding_allowed: bool
    crypto_funding_allowed: bool
    use_creator_fiat_payout: bool
    use_creator_crypto_payout: bool
    crypto_payout_address: Optional[str] = None
    fiat_payout_details: Optional[str] = None

    tags: List[str] | None = None

    team_members: List[TeamMemberIn] = []

    is_sponsored: bool
    sponsored_by: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    milestones: List[MilestoneIn] = []

    contact: ContactIn



class ProjectCardSchema(BaseModel):
    id: int
    title: str
    one_line: Optional[str]
    blurb: Optional[str]
    cover_image: Optional[str]
    tags: List[str] = []
    likes: int = 0
    views: int = 0
    comments: int = 0
    featured: bool = False
    trending: bool = False
    creator: CreatorSchema


class LikeStatusSchema(Schema):
    liked: bool
    like_count: int