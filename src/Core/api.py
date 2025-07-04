from ninja import NinjaAPI, Schema

from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/campaigns/", "campaigns.api.router")
api.add_router("/accounts/", "accounts.api.router")
api.add_router("/payments/", "payments.api.router")

