import stripe
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from campaigns.models import CampaignEntry  # ✅ update this import to your model


stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt  # for now — only during testing
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = int(float(data.get('amount', 0)) * 100)  # convert dollars to cents
            campaign_id = data.get('campaign_id')

            # ✅ 1. Get the campaign name
            campaign = CampaignEntry.objects.get(id=campaign_id)
            campaign_name = campaign.title



            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': amount,
                        'product_data': {
                            'name': f'Donation to {campaign_name}',  # ✅ dynamic title
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://localhost:3000/success',
                cancel_url=f'http://localhost:3000/campaigns/{campaign_id}',
                metadata={'campaign_id': campaign_id},
            )

            return JsonResponse({'url': session.url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
