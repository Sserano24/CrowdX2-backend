from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from Core import settings

# Create your models here.


 
class CampaignEntry(models.Model):
    title = models.CharField(max_length=255, unique=True)  # Campaign title
    description = models.TextField()  # Detailed campaign description
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Campaign goal (if fundraising)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Amount raised
    start_date = models.DateTimeField(default=timezone.now)  # Start date
    end_date = models.DateTimeField(null=True, blank=True)  # End date (optional)
    #status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")  # Campaign status
    #creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="campaigns")  # User who created the campaign
    creator = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="created_entries",
    null=True,  # ✅ Temporarily allow nulls
    blank=True
)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp when updated

class Campaign(models.Model):
    """A crowdfunding campaign created by a student or team."""

    # --- Core campaign info ---
    title = models.CharField(max_length=100)
    description = models.TextField()
    school = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional school/university name for context",
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated list of tags/skills/technologies",
    )

    # --- Ownership & team ---
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_campaigns",
        help_text="The primary user who created the campaign",
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="campaign_teams",
        blank=True,
        help_text="Other users who are part of this campaign team",
    )

    # --- Funding details ---
    goal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Funding target in USD (or equivalent)",
    )
    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total raised so far",
    )

    # --- Sponsorship ---
    sponsored_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Sponsor name or organization (optional)",
    )

    # --- Milestones ---
    milestones = models.JSONField(
        blank=True,
        null=True,
        help_text="List of milestone objects (title, done)",
    )

    # --- Status & lifecycle ---
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Engagement / activity signals ---
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    backer_count_24h = models.PositiveIntegerField(default=0, help_text="New backers in last 24h")
    donation_sum_24h = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Donations in the last 24h",
    )
    recruiter_saves = models.PositiveIntegerField(
        default=0, help_text="Times this campaign was bookmarked by recruiters"
    )

    # --- Ranking / trending ---
    trending_score = models.FloatField(default=0.0)
    last_activity_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title