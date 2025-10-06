from ninja import Router
from .schemas import CheckoutRequest, CheckoutResponse
from .services import create_stripe_checkout

router = Router()

@router.post("/checkout", response=CheckoutResponse)
def stripe_checkout(request, payload: CheckoutRequest):
    url = create_stripe_checkout(payload.amount, payload.campaign_id)
    return {"url": url}

from django.http import HttpRequest
from .services import get_or_create_connect_account, create_onboarding_link

router = Router(tags=["payments"])

@router.post("/connect/start")
def start_connect_onboarding(request: HttpRequest):
    # user = request.user  # ensure auth middleware
    user  = 0
    acct = get_or_create_connect_account(user)
    url  = create_onboarding_link(acct.account_id, request)
    return {"onboarding_url": url}
