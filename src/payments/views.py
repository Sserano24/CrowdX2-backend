# payments/views.py

from django.conf import settings
from django.shortcuts import redirect
from django.views import View
import stripe
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        YOUR_DOMAIN = "http://127.0.0.1:8000"
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'CrowdX Campaign Contribution',
                    },
                    'unit_amount': 5000,  # $50.00 in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=YOUR_DOMAIN + '/payments/success/',
            cancel_url=YOUR_DOMAIN + '/payments/cancel/',
        )

        # Send a message to the WebSocket when a session is created
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'payment_status',
            {
                'type': 'send_status',
                'message': 'A new payment session has been created!',
            }
        )

        return redirect(checkout_session.url, code=303)
