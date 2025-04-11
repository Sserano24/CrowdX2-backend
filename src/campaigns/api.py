from typing import List
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from .models import *
from .schemas import *

router = Router()

#@router.get("", response = List[CampaignEntryListSchema], auth= JWTAuth())
@router.get("", response=List[CampaignEntryListSchema])
def list_campaigns_entries(request):
    qs = CampaignEntry.objects.all()
    return qs

# <<<<<<< HEAD
# @router.get("{entry_id}/", response = CampaignEntryDetailSchema, auth= JWTAuth())
# def get_campaign_entry(request, entry_id:int):
#     obj = get_object_or_404(CampaignEntry, id = entry_id)
#     return obj

# @router.get("/me/campaigns", response=UserWithCampaignsSchema, auth=JWTAuth())
# def get_user_with_campaigns(request):
#     user = request.user
#     return {
#         "id": user.id,
#         "username": user.username,
#         "campaigns": user.campaigns.all()
#     }

@router.get("/me/campaigns", response=UserWithCampaignsSchema)
def get_user_with_campaigns(request):
    user = request.user
    return {
        "id": user.id,
        "username": user.username,
        "campaigns": user.campaigns.all()
    }

#@router.get("{entry_id}/", response = CampaignEntryDetailSchema, auth= JWTAuth())
@router.get("{entry_id}/", response=CampaignEntryDetailSchema)
def get_campaign_entry(request, entry_id: int):
    obj = get_object_or_404(CampaignEntry, id=entry_id)
    return obj
