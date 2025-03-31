from ninja import Router
from .schemas import CheckoutRequest, CheckoutResponse
from .services import create_stripe_checkout

router = Router()

@router.post("/checkout", response=CheckoutResponse)
def stripe_checkout(request, payload: CheckoutRequest):
    url = create_stripe_checkout(payload.amount)
    return {"url": url}
