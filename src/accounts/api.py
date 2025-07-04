from ninja import Router
from django.contrib.auth import get_user_model
from ninja_jwt.authentication import JWTAuth
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
    )

# ✅ Update profile with JWT
@router.put("/update", response=AccountSuccessfulResponse, auth=JWTAuth())
def update_profile(request, data: UserSchema):
    user = request.user
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(user, attr, value)
    user.save()
    return {"message": "User updated successfully"}

# ✅ Keep registration (open/public)
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
