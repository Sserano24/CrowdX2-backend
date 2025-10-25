from datetime import datetime
from decimal import Decimal
from ninja import Schema
from typing import List, Optional
from datetime import date
from .models import Campaign



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
    
from typing import List

class UserWithCampaignsSchema(Schema):
    id: int
    username: str
    campaigns: List[CampaignEntryListSchema]

from ninja import Schema
from datetime import datetime

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
