# from ninja import NinjaAPI, Schema

# from ninja_extra import NinjaExtraAPI
# from ninja_jwt.authentication import JWTAuth
# from ninja_jwt.controller import NinjaJWTDefaultController

# api = NinjaExtraAPI()
# api.register_controllers(NinjaJWTDefaultController)
# api.add_router("/campaigns/", "campaigns.api.router")
# api.add_router("/accounts/", "accounts.api.router")
# api.add_router("/payments/", "payments.api.router")

# Core/api.py
from ninja_extra import NinjaExtraAPI  # or from ninja import NinjaAPI (pick ONE)
from campaigns.api import router as campaigns_router
from accounts.api import router as accounts_router
from payments.api import router as payments_router

api = NinjaExtraAPI(version="1.0.0")  # or NinjaAPI, just be consistent

api.add_router("/campaigns", campaigns_router)
api.add_router("/accounts", accounts_router)
api.add_router("/payments", payments_router)
