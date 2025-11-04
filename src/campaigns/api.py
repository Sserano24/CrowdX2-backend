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


User = get_user_model()


# Detailed campaign info for frontend (with JWTAuth)
@router.get("/detailed/{campaign_id}", response=CampaignSchema, auth=JWTAuth())
def get_campaign_detail(request, campaign_id: int):
    """
    Return a single campaign with full detail; requires valid JWT token.
    Loads from the real Campaign model using campaign_id.
    """

    campaign = get_object_or_404(
        Campaign.objects
        .select_related("creator")  # FK to User
        .prefetch_related(
            "images",      # CampaignImage related_name="images"
            "milestones",  # CampaignMilestone related_name="milestones"
            # Only keep these if they actually exist on your model:
            # "tags",
            # "team_members",
        ),
        id=campaign_id,
    )

    # ----- Creator -----
    creator_user = campaign.creator
    creator = CreatorSchema(
        id=creator_user.id,
        name=(
            creator_user.get_full_name()
            or creator_user.username
            or creator_user.email
        ),
        # adjust to whatever field you actually store linkedin in:
        linkedin=getattr(creator_user, "linkedin", None) or getattr(creator_user, "link", None),
    )

    # ----- Team members (if you have a related model) -----
    # Team members (ManyToMany to User)
    if hasattr(campaign, "team_members"):
        team_members = []
        for tm in campaign.team_members.all():
            # Try to get linked student profile if it exists
            student_profile = getattr(tm, "student_profile", None)

            team_members.append(
                TeamMemberSchema(
                    id=tm.id,
                    # Combine first and last name if available, fallback to username or email
                    name=(tm.get_full_name() or tm.username or tm.email),
                    role=getattr(tm, "role", "") or "",
                    bio=getattr(tm, "bio", "") or "",
                    # Safely fetch linkedin from the student profile
                    linkedin=(
                        getattr(student_profile, "linkedin", None)
                        or getattr(student_profile, "portfolio_url", None)
                        or getattr(tm, "link", None)
                    ),
                )
            )
    else:
        team_members = []



    # ----- Milestones -----
    milestones = [
        MilestoneSchema(
            title=m.title,
            done=m.done,
            summary=m.summary or "",
        )
        for m in campaign.milestones.all()
    ]

    # ----- Tags (if you have Tag M2M) -----
    # Tags (safe for models with or without ManyToManyField)
    tags = []
    if hasattr(campaign, "tags"):
        try:
            tags = [getattr(t, "name", str(t)) for t in campaign.tags.all()]
        except Exception:
            tags = []


    # ----- Images -----
    # Your CampaignImage model uses "photo" (from admin code), so:
    images = [
        img.photo.url
        for img in campaign.images.all()
        if getattr(img, "photo", None) and hasattr(img.photo, "url")
    ]

    # ----- Contact info -----
    contact = ContactSchema(
        email=creator_user.email,
        github=getattr(campaign, "contact_github", None),
        youtube=getattr(campaign, "contact_youtube", None),
    )

    # ----- Build and return schema -----
    return CampaignSchema(
        id=campaign.id,
        title=campaign.title,
        school=campaign.school,
        one_line=campaign.blurb or "",
        project_summary=campaign.project_summary or "",

        problem_statement=campaign.problem_statement or "",
        proposed_solution=campaign.proposed_solution or "",
        technical_approach=campaign.technical_approach or "",
        implementation_progress=campaign.implementation_progress or "",
        impact_and_future_work=campaign.impact_and_future_work or "",
        mentorship_or_support_needs=campaign.mentorship_or_support_needs or "",

        goal_amount=int(campaign.goal_amount or 0),
        current_amount=int(campaign.current_amount or 0),

        tags=tags,
        images=images,

        creator=creator,
        team_members=team_members,

        is_sponsored=campaign.is_sponsored,
        sponsored_by=campaign.sponsored_by,

        start_date=campaign.start_date,
        end_date=campaign.end_date,

        milestones=milestones,           # 🔥 important: include milestones here

        verified=campaign.verified,
        contact=contact,
        outreach_message=campaign.outreach_message or "",
    )


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

@router.get("/student_campaigns/{id}")
def student_campaigns(request, id: int):
    """Return all active campaigns for a student (public)."""
    qs = Campaign.objects.filter(creator_id=id, is_active=True).order_by("-created_at")
    return [c.to_card_dict() for c in qs]
























