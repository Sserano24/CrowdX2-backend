from django.db import models
from campaigns.models import Campaign
from django.conf import settings



class Transaction(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField()
    stripe_session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.amount} to Campaign {self.campaign.id} on {self.created_at}"

class StripeConnectedAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_id = models.CharField(max_length=64, unique=True)
    details_submitted = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)