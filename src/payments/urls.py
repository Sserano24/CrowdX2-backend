from django.urls import path
from .views import create_paypal_order
from .webhooks import paypal_webhook

urlpatterns = [
    path('create-order/', create_paypal_order, name='create-order'),
    path('webhook/', paypal_webhook, name='paypal-webhook'),
]
