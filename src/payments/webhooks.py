# payments/webhooks.py
import stripe
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from campaigns.models import CampaignEntry
from payments.services import broadcast_campaign_update

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # TEMP: hardcoded for campaign ID 1
        c = CampaignEntry.objects.get(id=1)
        c.current_amount += 10
        c.save()

        broadcast_campaign_update(c.id, {
            "current_amount": float(c.current_amount),
            "goal_amount": float(c.goal_amount),
        })

    return HttpResponse(status=200)
