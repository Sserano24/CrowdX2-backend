# campaigns/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


def campaign_image_upload_to(instance, filename):
    return f"campaign_images/{instance.campaign_id}/{filename}"

class Campaign(models.Model):
    # --- identifiers / display ---
    one_line = models.CharField(max_length=255, blank=True, null=True)  # <--- add this

    title = models.CharField(max_length=100)

    # --- school theming ---
    school = models.CharField(max_length=255, blank=True, null=True)
    school_color_0 = models.CharField(max_length=32, blank=True, null=True)  # NEW
    school_color_1 = models.CharField(max_length=32, blank=True, null=True)  # NEW



    # --- badges ---
    verified = models.BooleanField(default=False)      # NEW
    is_sponsored = models.BooleanField(default=False)  # NEW
    sponsored_by = models.CharField(max_length=255, blank=True, null=True)

    # --- media ---
    cover_image = models.URLField(blank=True, null=True)  # NEW (fallback when no CampaignImage)
    # You also keep CampaignImage below

    # Detailed campaign description fields
    project_summary = models.TextField(blank=True, null=True)
    problem_statement = models.TextField(blank=True, null=True)
    proposed_solution = models.TextField(blank=True, null=True)
    technical_approach = models.TextField(blank=True, null=True)
    implementation_progress = models.TextField(blank=True, null=True)
    impact_and_future_work = models.TextField(blank=True, null=True)
    mentorship_or_support_needs = models.TextField(blank=True, null=True)

    outreach_message = models.TextField(blank=True, null=True)


    blurb = models.TextField(blank=True, null=True)  # NEW (short teaser)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")

    # --- ownership & team ---
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )

    def save(self, *args, **kwargs):
        # If the creator is a student, copy their school info
        if self.creator and self.creator.user_type == "student":
            profile = getattr(self.creator, "student_profile", None)
            if profile:
                self.school = self.school or profile.school
                self.school_color_0 = self.school_color_0 or getattr(profile, "school_color_0", None)
                self.school_color_1 = self.school_color_1 or getattr(profile, "school_color_1", None)
        super().save(*args, **kwargs)


    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CampaignTeamMember",
        related_name="campaign_memberships",
        blank=True,
    )

    # --- funding ---
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fiat_funding_allowed = models.BooleanField(default=False)
    crypto_funding_allowed = models.BooleanField(default=False)
    use_creator_fiat_payout = models.BooleanField(default=True)
    use_creator_crypto_payout = models.BooleanField(default=True)
    crypto_payout_address = models.CharField(
        max_length=128,
        blank=True,
    )
    fiat_payout_details = models.CharField(
        max_length=255,
        blank=True,
    )
    backers = models.PositiveIntegerField(default=0)   # NEW (if you track it)

    #links
    contact_email = models.EmailField(blank=True)
    contact_github = models.URLField(blank=True)
    contact_youtube = models.URLField(blank=True)

    # --- timing ---
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    # --- status / activity (you already had these) ---
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    backer_count_24h = models.PositiveIntegerField(default=0)
    donation_sum_24h = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recruiter_saves = models.PositiveIntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    last_activity_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CampaignMilestone(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="milestones",
    )

    # 1) Title of the milestone
    title = models.CharField(max_length=255)

    # 2) Details / description of the milestone
    details = models.TextField(blank=True, null=True)

    # 3) Status: done / not done (rename of your `done` field)
    status = models.BooleanField(default=False)

    #4) USD Milestone Amount 
    milestone_goal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        # icon = "✓" if self.status else "✗"
        return f"{self.title}"


class CampaignImage(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to="campaigns/",  
        blank=True,
        null=True,
    )
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.campaign.title} image #{self.pk}"
    
class CampaignTeamMember(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="team_member_links",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaign_team_links",
    )
    role = models.CharField(max_length=128, blank=True)

    class Meta:
        unique_together = ("campaign", "user")
