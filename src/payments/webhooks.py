import stripe
from decimal import Decimal
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from campaigns.models import Campaign  # ✅ Using Campaign now
from payments.models import Transaction
from payments.services import broadcast_campaign_update

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("❌ Signature verification failed:", e)
        return HttpResponse(status=400)

    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            print("✅ Webhook triggered")
            print("Session metadata:", session.get("metadata"))

            stripe_session_id = session.get("id")
            amount = Decimal(session.get("amount_total", 0)) / 100
            metadata = session.get("metadata", {})
            campaign_id = metadata.get("campaign_id")

            # Debug: show available Campaigns
            print("📦 Campaigns in DB:")
            for c in Campaign.objects.all():
                print(f" - ID: {c.id}, Title: {getattr(c, 'title', 'n/a')}, Raised: {c.current_amount}")

            try:
                campaign = Campaign.objects.get(id=int(campaign_id))

                if not Transaction.objects.filter(stripe_session_id=stripe_session_id).exists():
                    Transaction.objects.create(
                        campaign_id=campaign.id,
                        amount=amount,
                        stripe_session_id=stripe_session_id
                    )

                    campaign.current_amount += amount
                    campaign.save()

                    print(f"✅ Saved new amount: {campaign.current_amount}")

                    # Verify save by re-querying
                    refetched = Campaign.objects.get(id=campaign.id)
                    print(f"📦 DB now says: {refetched.current_amount}")

                    broadcast_campaign_update(refetched.id, {
                        "current_amount": float(refetched.current_amount),
                        "goal_amount": float(refetched.goal_amount),
                    })

            except Campaign.DoesNotExist:
                print("❌ Campaign not found:", campaign_id)
                return HttpResponse(status=404)

    except Exception as e:
        print("❌ Error during webhook handling:", e)
        return HttpResponse(status=500)

    return HttpResponse(status=200)
