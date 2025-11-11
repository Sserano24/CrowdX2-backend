from typing import List, Optional
from ninja import Router,File
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Prefetch
from django.utils.dateparse import parse_date
from django.db import transaction

from ninja.errors import HttpError



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
        .select_related("creator")
        .prefetch_related(
            "images",          # CampaignImage related_name="images"
            "milestones",      # CampaignMilestone related_name="milestones"
            "team_member_links__user",  # if you use CampaignTeamMember through model
        ),
        id=campaign_id,
    )

    # ----- Creator -----
    creator_user = campaign.creator
    student_profile0 = getattr(creator_user, "student_profile", None)
    creator = CreatorSchema(
        id=creator_user.id,
        name=(
            creator_user.get_full_name()
            or creator_user.username
            or creator_user.email
        ),
        linkedin=getattr(student_profile0, "linkedin", None),
    )

    # ----- Team members -----
    team_members: list[TeamMemberSchema] = []

    # If you have a through model like CampaignTeamMember with related_name="team_member_links"
    if hasattr(campaign, "team_member_links"):
        for link in campaign.team_member_links.select_related("user").all():
            u = link.user
            student_profile = getattr(u, "student_profile", None)
            team_members.append(
                TeamMemberSchema(
                    id=u.id,
                    name=(u.get_full_name() or u.username or u.email),
                    role=(link.role or ""),
                    bio=getattr(u, "bio", "") or "",
                    linkedin=(
                        getattr(student_profile, "linkedin", None)
                        or getattr(student_profile, "portfolio_url", None)
                        or getattr(u, "link", None)
                    ),
                )
            )
    # Fallback: old-style ManyToMany directly on campaign.team_members
    elif hasattr(campaign, "team_members"):
        for tm in campaign.team_members.all():
            student_profile = getattr(tm, "student_profile", None)
            team_members.append(
                TeamMemberSchema(
                    id=tm.id,
                    name=(tm.get_full_name() or tm.username or tm.email),
                    role=getattr(tm, "role", "") or "",
                    bio=getattr(tm, "bio", "") or "",
                    linkedin=(
                        getattr(student_profile, "linkedin", None)
                        or getattr(student_profile, "portfolio_url", None)
                        or getattr(tm, "link", None)
                    ),
                )
            )

    # ----- Milestones -----
    milestones = [
        MilestoneSchema(
            title=m.title,
            status=m.status,
            details=m.details or "",
        )
        for m in campaign.milestones.all()
    ]

    # ----- Tags -----
    raw_tags = campaign.tags or ""
    tags_list = [t.strip() for t in raw_tags.split(",") if t.strip()]

    # ----- Images (Azure-backed ImageField: "image") -----
    images = [
        CampaignImageSchema(
            id=img.id,
            url=img.image.url if getattr(img, "image", None) and hasattr(img.image, "url") else "",
            caption=img.caption or "",
        )
        for img in campaign.images.all().order_by("sort_order", "id")
    ]

    # ----- Contact info -----
    contact = ContactSchema(
        email=getattr(campaign, "contact_email", None) or creator_user.email,
        github=getattr(campaign, "contact_github", None),
        youtube=getattr(campaign, "contact_youtube", None),
    )

    # ----- Build and return full campaign schema -----
    return CampaignSchema(
        id=campaign.id,
        title=campaign.title,
        school=getattr(campaign, "school", ""),
        one_line=getattr(campaign, "one_line", "") or "",
        project_summary=campaign.project_summary or "",

        problem_statement=campaign.problem_statement or "",
        proposed_solution=campaign.proposed_solution or "",
        technical_approach=campaign.technical_approach or "",
        implementation_progress=campaign.implementation_progress or "",
        impact_and_future_work=campaign.impact_and_future_work or "",
        mentorship_or_support_needs=campaign.mentorship_or_support_needs or "",

        goal_amount=int(campaign.goal_amount or 0),
        current_amount=int(getattr(campaign, "current_amount", 0) or 0),

        tags=tags_list,
        images=images,                 # 👈 now a list[str], not objects

        creator=creator,
        team_members=team_members,

        is_sponsored=campaign.is_sponsored,
        sponsored_by=campaign.sponsored_by,

        start_date=campaign.start_date,
        end_date=campaign.end_date,

        milestones=milestones,
        verified=getattr(campaign, "verified", False),
        contact=contact,
        outreach_message=getattr(campaign, "outreach_message", "") or "",
    )



@router.post("/create", auth=JWTAuth())
@transaction.atomic
def create_campaign(request, payload: CampaignCreateSchema):
    if not request.user or not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    user = request.user  # This MUST be a real User, not AnonymousUser

    # --- Determine final payout details ---
    # Use creator’s stored info if the "use_creator" flags are true
    if payload.use_creator_fiat_payout:
        # use the creator’s saved fiat payout address
        fiat_payout_details = getattr(user, "fiat_payout_address", "") or ""
    else:
        fiat_payout_details = payload.fiat_payout_details

    if payload.use_creator_crypto_payout:
        crypto_payout_address = getattr(user, "crypto_wallet_address", "") or ""
    else:
        crypto_payout_address = payload.crypto_payout_address

    # --- Create the campaign ---
    campaign = Campaign.objects.create(
        creator=user,
        title=payload.title,
        school=getattr(user, "student_profile", None) and getattr(user.student_profile, "school", ""),
        one_line=payload.one_line,
        project_summary=payload.project_summary,
        problem_statement=payload.problem_statement,
        proposed_solution=payload.proposed_solution,
        technical_approach=payload.technical_approach,
        implementation_progress=payload.implementation_progress,
        impact_and_future_work=payload.impact_and_future_work,
        mentorship_or_support_needs=payload.mentorship_or_support_needs,

        goal_amount=payload.goal_amount,
        fiat_funding_allowed=payload.fiat_funding_allowed,
        crypto_funding_allowed=payload.crypto_funding_allowed,

        # store both the flags and the final resolved values
        use_creator_fiat_payout=payload.use_creator_fiat_payout,
        use_creator_crypto_payout=payload.use_creator_crypto_payout,
        fiat_payout_details=fiat_payout_details,
        crypto_payout_address=crypto_payout_address,

        tags=payload.tags,
        is_sponsored=payload.is_sponsored,
        sponsored_by=payload.sponsored_by or "",
        start_date=payload.start_date,
        end_date=payload.end_date,

        contact_email=(payload.contact.email or "").strip(),
        contact_github=(payload.contact.github or "").strip(),
        contact_youtube=(payload.contact.youtube or "").strip(),
    )

    # --- Team Members ---
    for tm in payload.team_members:
        member = get_object_or_404(User, id=tm.id)
        CampaignTeamMember.objects.create(
            campaign=campaign,
            user=member,
            role=(tm.role or "").strip(),
        )

    # --- Milestones ---
    for m in payload.milestones:
        CampaignMilestone.objects.create(
            campaign=campaign,
            title=m.title.strip(),
            status=m.status,
            details=(m.details or "").strip(),
            milestone_goal=m.milestone_goal,
        )

    return {"id": campaign.id}




@router.post("/{campaign_id}/images/upload", auth=JWTAuth())
def upload_campaign_image(
    request,
    campaign_id: int,
    file: UploadedFile = File(...),
):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    # Optional: only allow owner
    if campaign.creator_id != request.user.id:
        return 403, {"detail": "Not allowed to modify this campaign"}

    img = CampaignImage.objects.create(
        campaign=campaign,
        image=file,  # this triggers upload to Azure
    )

    return {
        "id": img.id,
        "url": img.image.url,  # full Azure Blob URL
        "caption": img.caption,
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

@router.get("/student_campaigns/{id}")
def student_campaigns(request, id: int):
    """Return all active campaigns for a student (public)."""
    qs = Campaign.objects.filter(creator_id=id, is_active=True).order_by("-created_at")
    return [c.to_card_dict() for c in qs]
























