from ninja import Schema

class CheckoutRequest(Schema):
    amount: float
    campaign_id: int  # ✅ Required so we can log to the right campaign

class CheckoutResponse(Schema):
    url: str
