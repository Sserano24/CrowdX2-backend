# src/payments/routing.py
from django.urls import re_path
from payments.consumers import CampaignConsumer

websocket_urlpatterns = [
    re_path(r'ws/campaigns/(?P<campaign_id>\d+)/$', CampaignConsumer.as_asgi()),
]


