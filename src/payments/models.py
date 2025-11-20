from django.db import models
from campaigns.models import Campaign
from django.conf import settings


class Transaction(models.Model):
    PAYMENT_METHODS = [
        ('paypal', 'PayPal'),
        ('manual', 'Manual'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paypal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Failed')
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True)  # Track PayPal order IDs
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.amount} via {self.payment_method} for Campaign {self.campaign.id}"
