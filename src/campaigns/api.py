from typing import List, Optional
from ninja import Router,File
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q, F, FloatField, ExpressionWrapper, Value
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Prefetch
from django.utils.dateparse import parse_date
from django.db import transaction
from django.db.models.functions import Coalesce, NullIf


from ninja.errors import HttpError
from .schemas import *

router = Router()


def _csv_to_list(value: str | None) -> list[str]:
    if not value:
        return []
    # split by comma, strip spaces, drop empties
    return [t.strip() for t in value.split(",") if t.strip()]


from .models import Campaign, CampaignImage

def _abs_url(request, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return url if url.startswith(("http://", "https://")) else request.build_absolute_uri(url)


def _image_url(request, image_field) -> str:
    """Return absolute URL for a Django ImageField (or '' if missing)."""
    if not image_field:
        return ""
    try:
        url = image_field.url  # may raise if no file
    except Exception:
        return ""
    return str(request.build_absolute_uri(url))  # ensure plain str


User = get_user_model()


# Detailed campaign info for frontend (with JWTAuth)
def _imagefield_url(request, image_field) -> str | None:
    """
    Safely extract absolute URL from an ImageField/FileField (or None).
    """
    if not image_field:
        return None
    try:
        url = image_field.url
    except Exception:
        return None
    return _abs_url(request, url)


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


@router.get("/student_campaigns/{id}")
def student_campaigns(request, id: int):
    """Return all active campaigns for a student (public)."""
    qs = Campaign.objects.filter(creator_id=id, is_active=True).order_by("-created_at")
    return [c.to_card_dict() for c in qs]


@router.get("/dash/myprojects", response=List[ProjectCardSchema])
def get_projects(request):
    """Return a list of projects formatted for ExploreProjectCard."""
    projects = Project.objects.select_related("creator").all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "one_line": p.one_line_summary,
            "blurb": p.description,
            "cover_image": p.cover_image.url if p.cover_image else None,
            "tags": [t.name for t in p.tags.all()] if hasattr(p, "tags") else [],
            "likes": getattr(p, "likes", 0),
            "views": getattr(p, "views", 0),
            "comments": getattr(p, "comment_count", 0),
            "featured": getattr(p, "featured", False),
            "trending": getattr(p, "trending", False),
            "creator": {
                "id": p.creator.id,
                "name": f"{p.creator.first_name} {p.creator.last_name}".strip()
                or p.creator.username,
                "avatar": getattr(p.creator, "profile_picture", None),
                "major": getattr(p.creator, "major", None),
                "school": getattr(p.creator, "school", None),
            },
        }
        for p in projects
    ]


@router.get("/search")
def search_campaigns(
    request,
    q: str = "",
    tags: Optional[str] = None,       # comma-separated
    school: Optional[str] = None,
    min_goal: Optional[int] = None,
    max_goal: Optional[int] = None,
    sort: str = "relevance",           # relevance | trending | newest | top_funded | most_viewed | most_liked
    page: int = 1,
    page_size: int = 12,
):
    

    qs = (
    Campaign.objects.all()
    .select_related("creator")
    .prefetch_related(
        Prefetch(
            "images",
            queryset=CampaignImage.objects.only("image", "sort_order").order_by("sort_order", "id"),
        )
    )
)

    # --- Text search (basic relevance using OR across key fields) ---
    if q:
        terms = [t.strip() for t in q.split() if t.strip()]
        for term in terms:
            qs = qs.filter(
                Q(title__icontains=term)
                | Q(one_line__icontains=term)
                | Q(description__icontains=term)
                | Q(school__icontains=term)
                | Q(creator__first_name__icontains=term)
                | Q(creator__last_name__icontains=term)
                | Q(tags__icontains=term)   # CSV tags field
            )

    # --- Filters ---
    if tags:
        for t in _csv_to_list(tags):
            qs = qs.filter(tags__icontains=t)

    if school:
        qs = qs.filter(school__icontains=school)

    if min_goal is not None:
        qs = qs.filter(goal_amount__gte=min_goal)

    if max_goal is not None:
        qs = qs.filter(goal_amount__lte=max_goal)

    # --- Annotations used by sorting ---
    funded_ratio = ExpressionWrapper(
        Coalesce(F("current_amount"), 0.0) / Coalesce(NullIf(F("goal_amount"), 0), 1.0),
        output_field=FloatField(),
    )
    qs = qs.annotate(funded_ratio=funded_ratio)

    # "trending_score" fallback if you don't store one:
    # views have small weight; likes a bit more; funding progress helps; newer gets a tiny boost
    recency_boost = ExpressionWrapper(
        # newer created_at => smaller diff => larger boost via 1/(days+1)
        Value(1.0) / (Coalesce((now() - F("created_at")), 0) / Value(86400.0) + Value(1.0)),
        output_field=FloatField(),
    )
    qs = qs.annotate(
        _hot=Coalesce(F("likes"), 0) * 1.0
             + Coalesce(F("views"), 0) * 0.1
             + Coalesce(funded_ratio, 0.0) * 50.0
             + recency_boost * 5.0
    )

    # --- Sorting ---
    sort = (sort or "relevance").lower()
    if sort in ("new", "newest"):
        qs = qs.order_by("-created_at")
    elif sort in ("funded", "top_funded"):
        qs = qs.order_by("-funded_ratio", "-current_amount")
    elif sort in ("views", "most_viewed"):
        qs = qs.order_by("-views")
    elif sort in ("likes", "most_liked"):
        qs = qs.order_by("-likes")
    elif sort in ("trending",):
        # If you have a stored trending_score, swap to order_by("-trending_score")
        qs = qs.order_by("-_hot")
    else:
        # "relevance" — crude: prioritize matches we already filtered by, then recency/hotness
        qs = qs.order_by("-_hot", "-created_at")

    # --- Pagination ---
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    # --- Build response payload tailored to ExploreProjectCard ---
    items = []
    today = now().date()

    for c in page_obj.object_list:
        # cover image + list of images (optional)
        cover_url = None
        image_urls: list[str] = []

        imgs = list(c.images.all())  # already ordered by sort_order, id
        if imgs:
            first = imgs[0]
            if getattr(first, "image", None):
                cover_url = _abs_url(request, first.image.url)

            for im in imgs[:6]:
                if getattr(im, "image", None):
                    image_urls.append(_abs_url(request, im.image.url))


        # days left
        days_left = 0
        if c.end_date:
            days_left = max((c.end_date - today).days, 0)

        # creator object expected by the card
        creator_name = (
            f"{getattr(c.creator, 'first_name', '')} {getattr(c.creator, 'last_name', '')}".strip()
            or getattr(c.creator, "username", "")
            or getattr(c.creator, "email", "Creator")
        )

        items.append(
            {
                "id": c.id,
                "title": c.title,
                "one_line": getattr(c, "one_line", None),
                "blurb": getattr(c, "description", None),
                "cover_image": cover_url,
                "images": [u for u in image_urls if u],
                "tags": _csv_to_list(getattr(c, "tags", "")),
                "likes": getattr(c, "likes", 0) or 0,
                "views": getattr(c, "views", 0) or 0,
                "comments": getattr(c, "comment_count", 0) or 0,
                "featured": getattr(c, "featured", False) or False,
                "trending": getattr(c, "trending", False) or False,
                "creator": {
                    "id": getattr(c.creator, "id", None),
                    "name": creator_name,
                    "avatar": getattr(c.creator, "profile_picture", None),
                    "major": getattr(c.creator, "major", None),
                    "school": getattr(c.creator, "school", None),
                },
                # Optional extras (used elsewhere on page)
                "school": getattr(c, "school", None),
                "current_amount": c.current_amount,
                "goal_amount": c.goal_amount,
                "backers": getattr(c, "backers", 0) or 0,
                "days_left": days_left,
            }
        )

    return {
        "items": items,
        "total": paginator.count,
        "page": page_obj.number,
        "page_size": page_obj.paginator.per_page,
    }

@router.get("/detailed/{campaign_id}", response=CampaignSchema, auth=JWTAuth())
def get_campaign_detail(request, campaign_id: int):
    campaign = get_object_or_404(
        Campaign.objects
        .select_related("creator")
        .prefetch_related(
            "images",
            "milestones",
            "team_member_links__user",
        ),
        id=campaign_id,
    )

    # ---------- Creator ----------
    creator_user = campaign.creator
    student_profile0 = getattr(creator_user, "student_profile", None)

    raw_tags = campaign.tags or "" 
    tags_list = [t.strip() for t in raw_tags.split(",") if t.strip()]

    avatar_url = (
        _imagefield_url(request, getattr(creator_user, "profile_picture", None))
        or _abs_url(request, getattr(creator_user, "profile_url", None))
        or None
    )

    creator = CreatorSchema(
        id=creator_user.id,
        name=(creator_user.get_full_name() or creator_user.username or creator_user.email),
        avatar=avatar_url or "",
        major=(getattr(student_profile0, "major", "") or ""),
        school=(getattr(student_profile0, "school", "") or ""),
        linkedin=(
            getattr(student_profile0, "linkedin", None)
            or getattr(student_profile0, "portfolio_url", None)
            or getattr(creator_user, "link", None)
        ),
    )

    # ---------- Team members ----------
    team_members: list[TeamMemberSchema] = []
    if hasattr(campaign, "team_member_links"):
        for link in campaign.team_member_links.select_related("user").all():
            u = link.user
            sp = getattr(u, "student_profile", None)
            avatar_tm = (
                _imagefield_url(request, getattr(u, "profile_picture", None))
                or _abs_url(request, getattr(u, "profile_url", None))
                or None
            )
            team_members.append(
                TeamMemberSchema(
                    id=u.id,
                    name=(u.get_full_name() or u.username or u.email),
                    role=(link.role or ""),
                    bio=getattr(u, "bio", "") or "",
                    linkedin=(
                        getattr(sp, "linkedin", None)
                        or getattr(sp, "portfolio_url", None)
                        or getattr(u, "link", None)
                    ),
                    avatar=avatar_tm or "",
                )
            )
    elif hasattr(campaign, "team_members"):
        for tm in campaign.team_members.all():
            sp = getattr(tm, "student_profile", None)
            avatar_tm = (
                _imagefield_url(request, getattr(tm, "profile_picture", None))
                or _abs_url(request, getattr(tm, "profile_url", None))
                or None
            )
            team_members.append(
                TeamMemberSchema(
                    id=tm.id,
                    name=(tm.get_full_name() or tm.username or tm.email),
                    role=getattr(tm, "role", "") or "",
                    bio=getattr(tm, "bio", "") or "",
                    linkedin=(
                        getattr(sp, "linkedin", None)
                        or getattr(sp, "portfolio_url", None)
                        or getattr(tm, "link", None)
                    ),
                    avatar=avatar_tm or "",
                )
            )

    # ---------- Images (return URLs only to match CampaignSchema.images: list[str]) ----------
    images = [
    CampaignImageSchema(
        id=img.id,
        url=_image_url(request, img.image),
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

    milestones = [
        MilestoneSchema(
            title=m.title,
            status=m.status,
            details=m.details or "",
        )
        for m in campaign.milestones.all()
    ]

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
        images=images,  # <<< now list[str], matches schema
        creator=creator,
        team_members=team_members,
        is_sponsored=campaign.is_sponsored,
        sponsored_by=campaign.sponsored_by,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        milestones=milestones,
        verified=getattr(campaign, "verified", False),
        contact=contact,
    )


















