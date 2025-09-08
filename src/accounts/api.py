from ninja import Router
from django.contrib.auth import get_user_model
from ninja_jwt.authentication import JWTAuth
from typing import List
from ninja.errors import HttpError
from .schemas import *

router = Router()
User = get_user_model()

@router.get("/user", response=UserSchema, auth=JWTAuth())
def user_detail(request):
    user = request.user

    # Safely return all expected fields defined in UserSchema
    return UserSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=getattr(user, "phone_number", None),
        bio=getattr(user, "bio", None),
        wallet_address=getattr(user, "wallet_address", None),
        links=getattr(user, "links", None),
        role= user.role,
    )

# Update profile with JWT
@router.put("/update", response=AccountSuccessfulResponse, auth=JWTAuth())
def update_profile(request, data: UserSchema):
    user = request.user
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(user, attr, value)
    user.save()
    return {"message": "User updated successfully"}

# Keep registration (open/public)
@router.post("/register")
def register(request, payload: registerUser):
    try:
        User.objects.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
        )
        return {"success": "User registered successfully"}
    except Exception as e:
        return {"error": str(e)}
    


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