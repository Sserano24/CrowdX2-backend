 # payments/routing.py
from django.urls import re_path
from .consumers import PaymentStatusConsumer

websocket_urlpatterns = [
    re_path(r'^ws/payment-status/$', PaymentStatusConsumer.as_asgi()),
]


