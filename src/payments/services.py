import paypalrestsdk
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# === PayPal Configuration ===
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

def create_paypal_payment(amount: float, description: str, return_url: str, cancel_url: str):
    """
    Creates a PayPal payment and returns the payment object (including approval URL).
    """
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
        "transactions": [{
            "amount": {"total": f"{amount:.2f}", "currency": "USD"},
            "description": description,
        }],
    })

    if payment.create():
        return payment
    else:
        raise Exception(f"PayPal Payment creation failed: {payment.error}")

def broadcast_campaign_update(campaign_id: int, data: dict):
    """
    Broadcasts a real-time campaign update to WebSocket clients.
    Triggered when a new donation or payment completes.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"campaign_{campaign_id}",
        {
            "type": "send_update",
            "data": data,
        }
    )
