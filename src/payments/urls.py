from django.urls import path
from .views import create_checkout_session
from django.shortcuts import render

urlpatterns = [
    path('', lambda request: render(request, 'payments/index.html'), name='index'),
    path('create-checkout-session/', create_checkout_session, name='create-checkout-session'),  # ✅ use your function here
    path('success/', lambda request: render(request, 'payments/success.html'), name='success'),
    path('cancel/', lambda request: render(request, 'payments/cancel.html'), name='cancel'),
]
