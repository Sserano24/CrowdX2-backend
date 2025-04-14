from django.db import models
from campaigns.models import CampaignEntry  # if you're linking to a campaign

class Transaction(models.Model):
    campaign = models.ForeignKey(CampaignEntry, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField()
    stripe_session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.amount} to Campaign {self.campaign.id} on {self.created_at}"
