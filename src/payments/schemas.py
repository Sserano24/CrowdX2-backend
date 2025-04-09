from ninja import Schema

class CheckoutRequest(Schema):
    amount: float

class CheckoutResponse(Schema):
    url: str