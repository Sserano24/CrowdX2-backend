from django.urls import path
from . import api, webhooks

urlpatterns = [
    path("paypal/create-order", api.create_paypal_order, name="create_order"),
    path("paypal/capture-order", api.capture_paypal_order, name="capture_order"),
    path("webhook/", webhooks.paypal_webhook, name="paypal_webhook"),
]

