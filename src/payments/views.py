import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import paypalrestsdk
from campaigns.models import Campaign

# Configure PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

@csrf_exempt
def create_paypal_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        campaign_id = data.get('campaign_id')

        campaign = Campaign.objects.get(id=campaign_id)

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"http://localhost:3000/success?campaign_id={campaign_id}",
                "cancel_url": f"http://localhost:3000/campaigns/{campaign_id}",
            },
            "transactions": [{
                "amount": {"total": f"{amount:.2f}", "currency": "USD"},
                "description": f"Donation to {campaign.title}",
            }],
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return JsonResponse({"url": link.href})
            return JsonResponse({'error': 'No approval URL found'}, status=400)
        else:
            return JsonResponse({'error': payment.error}, status=400)

    except Campaign.DoesNotExist:
        return JsonResponse({'error': 'Campaign not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
