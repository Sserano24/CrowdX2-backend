 
# payments/urls.py (NO WebSocket URL here)

from django.urls import path
from .views import CreateCheckoutSessionView
from django.shortcuts import render

urlpatterns = [
    path('', lambda request: render(request, 'payments/index.html'), name='index'),
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('success/', lambda request: render(request, 'payments/success.html'), name='success'),
    path('cancel/', lambda request: render(request, 'payments/cancel.html'), name='cancel'),
]


