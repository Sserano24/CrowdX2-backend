import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_checkout(amount: float, campaign_id: int) -> str:
    amount_cents = int(amount * 100)
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': amount_cents,
                'product_data': {
                    'name': 'CrowdX Campaign Contribution'
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"http://localhost:3000/success?campaign_id={campaign_id}",  # ✅ dynamic
        cancel_url=f'http://localhost:3000/cancel?campaign_id={campaign_id}',    # ✅ dynamic
        metadata={
            'campaign_id': str(campaign_id)
        }
    )
    return session.url

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_campaign_update(campaign_id: int, data: dict):
    """
    Broadcasts campaign donation updates over WebSocket.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'campaign_{campaign_id}',
        {
            'type': 'send_update',
            'data': data
        }
    )
