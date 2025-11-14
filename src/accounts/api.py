# accounts/api.py
from typing import List
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError, models
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from django.utils.text import slugify
from django.conf import settings

from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from django.core.exceptions import ObjectDoesNotExist

from .schemas import *
from .models import UserType as UserTypeEnum  # enum from your models

router = Router()
User = get_user_model()


def _image_url(request, image_field):
    """Return absolute URL for an ImageField (or None)."""
    if not image_field:
        return None
    try:
        url = image_field.url
    except ValueError:
        # file might not exist yet
        return None
    # If it's already absolute, just return it
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return request.build_absolute_uri(url)


def user_to_out(u) -> UserOut:
    # Build base
    data = dict(
        id=u.id,
        email=u.email,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        phone_number=getattr(u, "phone_number", None),
        bio=getattr(u, "bio", None),
        link=getattr(u, "link", None),  # <= singular, matches your model
        wallet_address=getattr(u, "wallet_address", None),
        user_type=u.user_type,
        blurb=getattr(u, "blurb", None),
        is_email_verified=getattr(u, "is_email_verified", False),
        student=None,
        professional=None,
    )

    # Pull related profiles if present
    sp = getattr(u, "student_profile", None)
    pp = getattr(u, "professional_profile", None)

    # Normalize user_type comparisons:
    # - If you're using a Pydantic enum with values "student"/"professional", this is fine.
    # - If you prefer, compare directly to strings: if u.user_type == "student": ...
    if u.user_type in ("student", getattr(UserTypeEnum, "STUDENT", "student")) and sp:
        data["student"] = StudentProfileOut(
            school=sp.school,
            major=sp.major,
            graduation_year=sp.graduation_year,
            gpa=float(sp.gpa) if sp.gpa is not None else None,
            linkedin=sp.linkedin or None,
        )

    if u.user_type in ("professional", getattr(UserTypeEnum, "PROFESSIONAL", "professional")) and pp:
        data["professional"] = ProfessionalProfileOut(
            company=pp.company,
            title=pp.title,
            linkedin_url=pp.linkedin_url or None,
            hiring=pp.hiring,
            interests=pp.interests,
        )

    return UserOut(**data)


# ---------- Endpoints ----------

# @router.get("/user", response=UserOut, auth=JWTAuth())
# def user_detail(request):
#     return user_to_out(request.user)


@router.put("/update", response=AccountSuccessfulResponse, auth=JWTAuth())
def update_profile(request, data: UserUpdate):
    u = request.user
    for attr, val in data.dict(exclude_unset=True).items():
        setattr(u, attr, val)
    u.save()
    return {"message": "User updated successfully"}


@router.post("/register", response=UserOut)
@transaction.atomic
def register(request, payload: RegisterUser):
    if payload.user_type not in ("student", "professional"):
        raise HttpError(400, "user_type must be 'student' or 'professional'")

    if payload.user_type == "student" and not payload.student:
        raise HttpError(400, "student payload required for user_type=student")
    if payload.user_type == "professional" and not payload.professional:
        raise HttpError(400, "professional payload required for user_type=professional")

    try:
        u = User.objects.create_user(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
        )
    except IntegrityError:
        raise HttpError(400, "User with this email/username already exists.")

    u.user_type = payload.user_type
    u.bio = payload.bio
    u.link = payload.link
    u.wallet_address = payload.wallet_address

    # optional: URL-based profile image
    if getattr(payload, "profile_image", None):
        u.profile_image = payload.profile_image

    u.save()

    if payload.user_type == "student":
        from .models import StudentProfile
        sp = payload.student
        StudentProfile.objects.create(
            user=u,
            school=sp.school,
            major=sp.major or "",
            graduation_year=sp.graduation_year,
            gpa=sp.gpa,
            linkedin=sp.portfolio_url or "",
        )
    else:
        from .models import ProfessionalProfile
        pp = payload.professional
        ProfessionalProfile.objects.create(
            user=u,
            company=pp.company,
            title=pp.title or "",
            linkedin_url=pp.linkedin_url or "",
            hiring=bool(pp.hiring) if pp.hiring is not None else False,
            interests=pp.interests or "",
        )

    return user_to_out(u)

@router.post("/profile/avatar", auth=JWTAuth())
def upload_avatar(request, file: UploadedFile = File(...)):
    user = request.user  # current logged-in user

    # Save to your ImageField (adjust field name as needed)
    user.profile_image.save(file.name, file, save=True)

    # If you have a helper to build full URLs:
    avatar_url = _image_url(request, user.profile_image)

    return {"avatar_url": avatar_url}



# @router.get("/spotlight_users", response=List[UserOut])
# def get_spotlight_users(request):
#     users = (
#         User.objects
#         .filter(is_active=True)
#         .order_by("-user_score")[:4]
#     )

#     return [
#         {
#             "id": u.id,
#             # Full first name + first letter of last name (with dot), guarded if last_name is empty
#             "name": f"{u.first_name} {u.last_name[0] + '.' if u.last_name else ''}",
#             "profile_picture": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=1600&auto=format&fit=crop",
#             "blurb": u.blurb,
#             # Your property already returns values("id","title") → list of dicts
#             "associated_projects": list(u.associated_campaigns),
#         }
#         for u in users
#     ]


@router.get("/users/recent")
def recent_users(request):
    # Get last 4 created users
    users = User.objects.filter(user_type="student").order_by("-id")[:4]


    return {
        "items": [
            {
                "id": u.id,
                "name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "major": getattr(u.student, "major", None) if hasattr(u, "student") else None,
                "school": getattr(u.student, "school", None) if hasattr(u, "student") else None,
                "profile_image": (
                    request.build_absolute_uri(u.profile_image.url)
                    if getattr(u, "profile_image", None)
                    and getattr(u.profile_image, "url", None)
                    else None
                ),
                "tags": [
                    t.strip()
                    for t in (getattr(u.student, "tags", "") or "").split(",")
                    if t.strip()
                ] if hasattr(u, "student") else [],
                "bio": u.bio or "",
                # Use .campaigns.count() only if you set related_name="campaigns"
                "projectsCount": u.campaigns.count(),
            }
            for u in users
        ]
    }



@router.get("/profile/{id}", auth=JWTAuth())
def get_user_profile(request, id: int):
    """Return a profile; requires valid JWT token."""
    user = get_object_or_404(User, id=id)

    # Base info (shared by all user types)
    data = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile_picture": _image_url(request, getattr(user, "profile_image", None)),
        "email": user.email,
        "bio": user.bio,
        "user_type": user.user_type,
        "wallet_address": user.wallet_address,
        "link": user.link,
        "is_email_verified": user.is_email_verified,
        "user_score": user.user_score,
    }

    # Add fields depending on user type
    if user.user_type == "student":
        profile = getattr(user, "student_profile", None)
        data.update({
            "school": getattr(profile, "school", None),
            "school_color_0": getattr(profile, "school_color_0", None),
            "school_color_1": getattr(profile, "school_color_1", None),
            "major": getattr(profile, "major", None),
            "graduation_year": getattr(profile, "graduation_year", None),
            "gpa": getattr(profile, "gpa", None),
            "linkedin": getattr(profile, "linkedin", None),
            "github": getattr(profile, "github", None),
            "active_project_count": getattr(profile, "active_project_count", None),
            "total_funds_raised": getattr(profile, "total_funds_raised", None),
            "co_creator_count": getattr(profile, "co_creator_count", None),

        })

    elif user.user_type == "professional":
        # Example — customize with your ProfessionalProfile model fields
        profile = getattr(user, "professional_profile", None)
        data.update({
            "company": getattr(profile, "company", None),
            "title": getattr(profile, "title", None),
            "linkedin": getattr(profile, "linkedin", None),
            "hiring": getattr(profile, "hiring", None),
            "interests": getattr(profile, "interests", None),
        })

    # Optional: include creator flag if viewing another profile
    data["is_creator_viewing"] = request.user.id != user.id

    return data

@router.get("/search", response=list[UserSearchResult])
def search_users(request, query: str = ""):
    q = query.strip()
    if not q:
        return []

    qs = (
        User.objects.filter(is_active=True)
        .filter(
            models.Q(first_name__icontains=q)
            | models.Q(last_name__icontains=q)
            | models.Q(email__icontains=q)
        )
        .order_by("-featured", "-trending",)[:10]
    )


    results = [
        UserSearchResult(
            id=user.id,
            name=f"{user.first_name} {user.last_name}".strip() or user.email,
            email=user.email,
        )
        for user in qs
    ]
    return results


def make_guest_username(email: str) -> str:
    base = slugify(email.split("@")[0]) or "guest"
    i = 0
    username = base
    while User.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username

@router.post("/guest/register")
@transaction.atomic
def guest_register(request, payload: GuestRegisterIn):
    user, created = User.objects.get_or_create(
        email=payload.email,
        defaults={
            "username": make_guest_username(payload.email),
            "first_name": payload.first_name or "",
            "last_name": payload.last_name or "",
            "user_type": UserTypeEnum.GUEST,  # ✅ now definitely the TextChoices
        },
    )

    if created:
        user.set_unusable_password()
        user.save()

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": user.user_type,
    }

@router.get("/navbar", auth=JWTAuth())
def get_current_user(request):
    """Return the currently authenticated user's id and type."""
    user = request.user
    return {
        "id": user.id,
        "email": user.email,
        "user_type": user.user_type,
    }
