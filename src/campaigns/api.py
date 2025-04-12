from typing import List
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from .models import *
from .schemas import *

router = Router()

# Public route to list all campaign entries
@router.get("", response=List[CampaignEntryListSchema])
def list_campaigns_entries(request):
    return CampaignEntry.objects.all()

@router.get("/mine", response=List[CampaignOut], auth=JWTAuth())
def my_campaigns(request):
    print("📥 /mine endpoint hit")

    # Confirm user from JWT
    print("🔐 Authenticated user:", request.user)

    # Query campaigns from DB
    campaigns = Campaign.objects.filter(creator=request.user)
    print(f"🔎 Found {campaigns.count()} campaigns")

    # See raw data returned (this will help detect serialization issues)
    for c in campaigns:
        print("📦 Campaign object:", {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "goal_amount": float(c.goal_amount),
            "current_amount": float(c.current_amount),
            "creator_id": c.creator_id,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        })

    # Return queryset normally (we can fallback to manual list later)
    return campaigns

# Optional route for user profile + campaigns
@router.get("/me/campaigns", response=UserWithCampaignsSchema, auth=JWTAuth())
def get_user_with_campaigns(request):
    user = request.user
    return {
        "id": user.id,
        "username": user.username,
        "campaigns": user.campaigns.all()
    }

# ✅ Dynamic route goes LAST to avoid matching '/mine' as an int
@router.get("entry/{entry_id}/", response=CampaignEntryDetailSchema)
def get_campaign_entry(request, entry_id: int):
    obj = get_object_or_404(CampaignEntry, id=entry_id)
    return obj
