from typing import List, Optional
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Prefetch
from django.utils.dateparse import parse_date
from django.db import transaction


from .models import *
from .schemas import *

router = Router()

def _csv_to_list(value: str | None) -> list[str]:
    if not value:
        return []
    # split by comma, strip spaces, drop empties
    return [t.strip() for t in value.split(",") if t.strip()]



# @router.get("/mine", response=List[CampaignOut], auth=JWTAuth())
# def my_campaigns(request):
#     print("📥 /mine endpoint hit")

#     # Confirm user from JWT
#     print("🔐 Authenticated user:", request.user)

#     # Query campaigns from DB
#     campaigns = Campaign.objects.filter(creator=request.user)
#     print(f"🔎 Found {campaigns.count()} campaigns")

#     # See raw data returned (this will help detect serialization issues)
#     for c in campaigns:
#         print("📦 Campaign object:", {
#             "id": c.id,
#             "title": c.title,
#             "description": c.description,
#             "goal_amount": float(c.goal_amount),
#             "current_amount": float(c.current_amount),
#             "creator_id": c.creator_id,
#             "created_at": c.created_at,
#             "updated_at": c.updated_at,
#         })

#     # Return queryset normally (we can fallback to manual list later)
#     return campaigns

@router.post("/createnew")
def create_campaign(request, payload: CampaignEntryCreateSchema):
    User = get_user_model()
    dummy = User.objects.first()
    # if not request.user or not request.user.is_authenticated:
    #     from ninja.errors import HttpError
    #     raise HttpError(401, "Authentication required")

    # Parse end_date string → date
    end_date = None
    if payload.end_date:
        end_date = parse_date(payload.end_date)

    # Create campaign object
    campaign = Campaign.objects.create(
        title=payload.title.strip(),
        description=payload.description.strip(),
        school=(payload.school or "").strip() or None,
        tags=(payload.tags or "").strip(),
        sponsored_by=(payload.sponsored_by or "").strip() or None,
        goal_amount=payload.goal_amount,
        end_date=end_date,
        creator=dummy,
        milestones=payload.milestones,
    )

    # Add team members if provided
    if payload.team_members:
        users = User.objects.filter(id__in=payload.team_members)
        campaign.team_members.add(*users)

    return {"message": "Campaign created successfully"}

# Optional route for user profile + campaigns
# @router.get("/me/campaigns", response=UserWithCampaignsSchema, auth=JWTAuth())
# def get_user_with_campaigns(request):
#     user = request.user
#     return {
#         "id": user.id,
#         "username": user.username,
#         "campaigns": user.campaigns.all()
#     }

# # ✅ Dynamic route goes LAST to avoid matching '/mine' as an int
# @router.get("campaign/{campaign_id}/", response=CampaignOut)
# def get_campaign(request, campaign_id: int):
#     campaign = get_object_or_404(Campaign, id=campaign_id)
#     return campaign

User = get_user_model()


# Detailed campaign info for frontend (with JWTAuth)
@router.get("/detail/{campaign_id}/", auth=JWTAuth())
def campaign_detail(request, campaign_id: int):
    # Pull creator/team/images efficiently
    c = get_object_or_404(
        Campaign.objects.select_related("creator").prefetch_related(
            Prefetch("team_members"),
            Prefetch("images"),  # CampaignImage FK with related_name="images"
        ),
        id=campaign_id,
    )

    # Build absolute URLs for all related images
    image_urls = []
    for img in c.images.all():
        try:
            if getattr(img.photo, "url", None):
                image_urls.append(request.build_absolute_uri(img.photo.url))
        except ValueError:
            # file missing on disk or misconfigured MEDIA settings
            pass

    return {
        "id": c.id,
        "title": c.title,
        "school": c.school,
        "description": c.description,
        "goal_amount": float(c.goal_amount),
        "current_amount": float(c.current_amount),
        "tags": [t.strip() for t in (c.tags or "").split(",") if t.strip()],
        "images": image_urls,  # now from CampaignImage rows
        "creator": {
            "id": c.creator.id,
            "name": getattr(c.creator, "username", str(c.creator)),
        },
        "team_members": [
            {"id": u.id, "name": getattr(u, "username", str(u))}
            for u in c.team_members.all()
        ],
        "is_sponsored": bool(c.sponsored_by),
        "sponsored_by": c.sponsored_by,
        "start_date": str(c.start_date),
        "end_date": str(c.end_date) if c.end_date else None,
        "milestones": c.milestones if c.milestones is not None else [],
        "verified": True,
    }


#stats for homepage
@router.get("/stats", response=StatsOut, auth=None)
def get_stats(request):

    active_campaigns_count = Campaign.objects.filter(is_active=True).count()
    active_creators_count = User.objects.filter(is_active=True).distinct().count()

    return {
        "active_projects": active_campaigns_count,
        "funds_raised": 200,
        "active_creators": active_creators_count,
    }


# Public route for spotlight campaigns
@router.get("/spotlight")
def spotlight(request):
    items = Campaign.objects.filter(is_active=True).order_by("-trending_score")[:3]
    return {
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description[:160],
                "school": c.school,
                "current_amount": float(c.current_amount),
                "goal_amount": float(c.goal_amount),
                "tags": [t.strip() for t in (c.tags or "").split(",") if t.strip()],
            }
            for c in items
        ]
    }
# Note: recompute_trending_scores() moved to services.py


@router.get("/search", response=SearchResponse)
def search_campaigns(
    request,
    q: str = "",
    tags: Optional[str] = None,
    school: Optional[str] = None,
    min_goal: Optional[int] = None,
    max_goal: Optional[int] = None,
    sort: str = "relevance",
    page: int = 1,
    page_size: int = 12,
):
    qs = (
        Campaign.objects.all()
        .prefetch_related(
            Prefetch(
                "images",
                queryset=CampaignImage.objects.only("photo").order_by("id"),
            )
        )
    )

    # Basic text search
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(school__icontains=q)
            | Q(tags__icontains=q)
        )

    if tags:
        wanted = [t.strip() for t in tags.split(",") if t.strip()]
        for t in wanted:
            qs = qs.filter(tags__icontains=t)

    if school:
        qs = qs.filter(school__icontains=school)

    if min_goal is not None:
        qs = qs.filter(goal_amount__gte=min_goal)
    if max_goal is not None:
        qs = qs.filter(goal_amount__lte=max_goal)

    # Sorting
    if sort == "new":
        qs = qs.order_by("-created_at")
    elif sort == "funded":
        qs = qs.order_by("-current_amount")
    elif sort == "trending":
        qs = qs.order_by("-trending_score")

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    items = []
    for c in page_obj.object_list:
        # first related image (prefetched)
        cover_url = None
        first_img = next(iter(c.images.all()), None)
        if first_img and getattr(first_img, "photo", None):
            url = first_img.photo.url
            # if storage returns absolute URL (e.g., S3), use as-is
            cover_url = url if url.startswith(("http://", "https://")) else request.build_absolute_uri(url)

        # days left
        days_left = 0
        if c.end_date:
            delta = (c.end_date - now().date()).days
            days_left = max(delta, 0)

        items.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "school": c.school,
            "current_amount": c.current_amount,
            "goal_amount": c.goal_amount,
            "tags": _csv_to_list(c.tags) or [],
            "cover_image": cover_url,   
            "backers": getattr(c, "backers", 0),
            "days_left": days_left,
        })

    return {
        "items": items,
        "total": paginator.count,
        "page": page_obj.number,
        "page_size": page_obj.paginator.per_page,
    }

@router.post("/campaigns", response=CampaignOut)
def create_campaign(request, payload: CampaignIn):
    # 1) Resolve creator
    creator = get_object_or_404(User, id=payload.creator_id)

    # 2) Create Campaign
    c = Campaign.objects.create(
        title=payload.title,
        description=payload.description,
        school=payload.school,
        tags=",".join(payload.tags) if payload.tags else "",
        creator=creator,
        goal_amount=payload.goal_amount,
        # optional fields
        end_date=payload.end_date,
        milestones=[m.dict() for m in payload.milestones] if payload.milestones else None,
        # other fields have defaults: current_amount, is_active, etc.
    )

    # 3) Team members (optional)
    if payload.team_member_ids:
        members = User.objects.filter(id__in=payload.team_member_ids)
        c.team_members.set(members)

    return CampaignOut.from_model(c)

























