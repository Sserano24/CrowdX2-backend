import json
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from campaigns.models import Campaign
from payments.models import Transaction
from payments.services import broadcast_campaign_update
import paypalrestsdk

# Configure PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

@csrf_exempt
def paypal_webhook(request):
    """
    Handle PayPal webhook or capture callback.
    """
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')
        resource = data.get('resource', {})

        if event_type == "PAYMENT.SALE.COMPLETED":
            payment_id = resource.get('parent_payment')
            amount = Decimal(resource['amount']['total'])
            currency = resource['amount']['currency']

            # Custom metadata is available only if you embed it at order creation
            campaign_id = resource.get('invoice_number')  # optional

            if not campaign_id:
                return HttpResponse(status=400)

            try:
                campaign = Campaign.objects.get(id=int(campaign_id))
                if not Transaction.objects.filter(payment_id=payment_id).exists():
                    Transaction.objects.create(
                        campaign=campaign,
                        amount=amount,
                        payment_id=payment_id
                    )
                    campaign.current_amount += amount
                    campaign.save()

                    broadcast_campaign_update(campaign.id, {
                        "current_amount": float(campaign.current_amount),
                        "goal_amount": float(campaign.goal_amount),
                    })
            except Campaign.DoesNotExist:
                return HttpResponse(status=404)

    except Exception as e:
        print("❌ Webhook error:", e)
        return JsonResponse({"error": str(e)}, status=500)

    return HttpResponse(status=200)
