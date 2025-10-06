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


from django.db import transaction
from django.urls import reverse
from django.conf import settings
from .stripe_client import stripe
from .models import StripeConnectedAccount

@transaction.atomic
def get_or_create_connect_account(user, email: str | None = None) -> StripeConnectedAccount:
    acct = StripeConnectedAccount.objects.filter(user=user).first()
    if acct:
        return acct

    account = stripe.Account.create(
        country="US",
        email=email or getattr(user, "email", None),
        controller={
            "fees": {"payer": "application"},          # your platform pays fees
            "losses": {"payments": "application"},
            "stripe_dashboard": {"type": "express"},   # Express accounts
        },
    )
    return StripeConnectedAccount.objects.create(
        user=user, account_id=account["id"],
        details_submitted=account.get("details_submitted", False),
        payouts_enabled=account.get("payouts_enabled", False),
    )

def create_onboarding_link(account_id: str, request) -> str:
    refresh_url = request.build_absolute_uri(reverse("stripe-onboard-refresh"))
    return_url  = request.build_absolute_uri(reverse("stripe-onboard-return"))
    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return link["url"]
