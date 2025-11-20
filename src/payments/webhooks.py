import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from payments.models import Transaction
from campaigns.models import Campaign
from payments.services import verify_paypal_webhook

@csrf_exempt
def paypal_webhook(request):
    """Handle incoming PayPal webhook events."""
    try:
        if not verify_paypal_webhook(request):
            return JsonResponse({"error": "Invalid PayPal webhook signature"}, status=400)

        payload = json.loads(request.body.decode("utf-8"))
        event_type = payload.get("event_type")
        resource = payload.get("resource", {})

        print(f"🔔 Received PayPal event: {event_type}")

        if event_type == "CHECKOUT.ORDER.APPROVED":
            order_id = resource.get("id")
            tx = Transaction.objects.filter(paypal_order_id=order_id).first()
            if tx:
                tx.status = "APPROVED"
                tx.save()

        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
            tx = Transaction.objects.filter(paypal_order_id=order_id).first()
            if tx:
                tx.status = "COMPLETED"
                tx.save()

                # Update campaign funds
                campaign = Campaign.objects.get(id=tx.campaign_id)
                campaign.current_amount += tx.amount
                campaign.save()
                print(f"✅ Updated campaign {campaign.id}: +${tx.amount}")

        return HttpResponse(status=200)

    except Exception as e:
        print(f"❌ PayPal webhook error: {e}")
        return JsonResponse({"error": str(e)}, status=400)

