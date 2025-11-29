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

    # 💰 Rename meaning: 'amount' = Gross amount
    amount = models.FloatField(help_text="Total amount charged (gross)")

    # ✅ New fields for fee + net amount
    fee = models.FloatField(null=True, blank=True, help_text="PayPal fee deducted")
    net_amount = models.FloatField(null=True, blank=True, help_text="Net amount received after PayPal fees")

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paypal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Failed')
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.net_amount or self.amount} via {self.payment_method} for Campaign {self.campaign.id}"

class Payout(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="payouts")

    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payout_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.25)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    paypal_batch_id = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payout #{self.id} – {self.campaign.title} – ${self.net_amount:.2f} ({self.status})"
