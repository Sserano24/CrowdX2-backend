from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from ninja_jwt.authentication import JWTAuth
from .models import *
from .schemas import *

router = Router()

@router.get("", response = List[CampaignEntryListSchema], auth= JWTAuth())
def list_campaigns_entries(request):
    qs = CampaignEntry.objects.all()
    return qs

@router.get("{entry_id}/", response = CampaignEntryDetailSchema, auth= JWTAuth())
def get_campaign_entry(request, entry_id:int):
    obj = get_object_or_404(CampaignEntry, id = entry_id)
    return obj