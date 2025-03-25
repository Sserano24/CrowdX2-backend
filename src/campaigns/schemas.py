from datetime import datetime
from decimal import Decimal
from ninja import Schema

# Schema for creating a new campaign entry
class CampaignEntryCreateSchema(Schema):
    title: str
    description: str
    goal_amount: Decimal
    start_date: datetime
    end_date: datetime | None = None  # Optional field

# Schema for retrieving campaign details (includes timestamps)
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

class CampaignEntryListSchema(Schema):
    id: int
    title: str
    description: str
    goal_amount: Decimal
    current_amount: Decimal
    start_date: datetime
    end_date: datetime | None = None  # Optional

