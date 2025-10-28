from ninja import Router
from .schemas import CheckoutRequest, CheckoutResponse
from .services import create_paypal_payment

router = Router()

@router.post("/checkout", response=CheckoutResponse)
def paypal_checkout(request, payload: CheckoutRequest):
    approval_url = create_paypal_payment(payload.amount, payload.campaign_id)
    return {"url": approval_url}
