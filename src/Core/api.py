from ninja import NinjaAPI, Schema

from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/campaigns/", "campaigns.api.router")
api.add_router("/accounts/", "accounts.api.router")
api.add_router("/payments/", "payments.api.router")


class UserSchema(Schema):
    username: str
    is_authenticated: bool
    email: str = None

@api.get("/hello")
def hello(request):
    print(request)
    return {"message": "Hello Mother Trucker"}

@api.get("/me", response=UserSchema, auth=JWTAuth())
def me(request):
    return request.user
