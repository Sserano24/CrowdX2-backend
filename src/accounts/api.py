# accounts/api.py
from typing import List
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .schemas import (
    UserOut,
    UserUpdate,
    RegisterUser,
    StudentProfileOut,
    ProfessionalProfileOut,
    AccountSuccessfulResponse,
)
from .models import UserType as UserTypeEnum  # enum from your models

router = Router()
User = get_user_model()


def user_to_out(u) -> UserOut:
    data = dict(
        id=u.id,
        email=u.email,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        phone_number=getattr(u, "phone_number", None),
        bio=getattr(u, "bio", None),
        links=getattr(u, "links", None),
        wallet_address=getattr(u, "wallet_address", None),
        role=u.role,
        user_type=u.user_type,
        blurb=getattr(u, "blurb", None),
        is_email_verified=getattr(u, "is_email_verified", False),
        student=None,
        professional=None,
    )

    # attach the correct profile if present
    if u.user_type == UserTypeEnum.STUDENT and hasattr(u, "student_profile"):
        sp = u.student_profile
        data["student"] = StudentProfileOut(
            school=sp.school,
            major=sp.major,
            graduation_year=sp.graduation_year,
            gpa=sp.gpa,
            portfolio_url=sp.portfolio_url,
        )
    elif u.user_type == UserTypeEnum.PROFESSIONAL and hasattr(u, "professional_profile"):
        pp = u.professional_profile
        data["professional"] = ProfessionalProfileOut(
            company=pp.company,
            title=pp.title,
            linkedin_url=pp.linkedin_url,
            hiring=pp.hiring,
            interests=pp.interests,
        )

    return UserOut(**data)


# ---------- Endpoints ----------

@router.get("/user", response=UserOut, auth=JWTAuth())
def user_detail(request):
    return user_to_out(request.user)


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
    # Require matching profile block
    if payload.user_type == "student" and not payload.student:
        raise HttpError(400, "student payload required for user_type=student")
    if payload.user_type == "professional" and not payload.professional:
        raise HttpError(400, "professional payload required for user_type=professional")

    # Create base user
    try:
        u = User.objects.create_user(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
        )
    except IntegrityError as e:
        # likely duplicate email/username
        raise HttpError(400, "User with this email/username already exists.")

    # Set common fields
    u.user_type = payload.user_type
    u.role = payload.role
    u.bio = payload.bio
    u.links = payload.links
    u.wallet_address = payload.wallet_address
    u.save()

    # Create the matching profile
    if payload.user_type == "student":
        from .models import StudentProfile
        sp = payload.student
        StudentProfile.objects.create(
            user=u,
            school=sp.school,
            major=sp.major or "",
            graduation_year=sp.graduation_year,
            gpa=sp.gpa,
            portfolio_url=sp.portfolio_url or "",
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


@router.get("/spotlight_users", response=List[UserOut])
def get_spotlight_users(request):
    users = (
        User.objects
        .filter(is_active=True)
        .order_by("-user_score")[:4]
    )

    return [
        {
            "id": u.id,
            # Full first name + first letter of last name (with dot), guarded if last_name is empty
            "name": f"{u.first_name} {u.last_name[0] + '.' if u.last_name else ''}",
            "profile_picture": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=1600&auto=format&fit=crop",
            "blurb": u.blurb,
            # Your property already returns values("id","title") → list of dicts
            "associated_projects": list(u.associated_campaigns),
        }
        for u in users
    ]