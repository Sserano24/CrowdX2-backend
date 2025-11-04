# campaigns/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

def campaign_image_upload_to(instance, filename):
    return f"campaign_images/{instance.campaign_id}/{filename}"

class Campaign(models.Model):
    # --- identifiers / display ---
    slug = models.SlugField(unique=True, blank=True)  # NEW (for /campaigns/<slug>)
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
        settings.AUTH_USER_MODEL,
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
        related_name="campaign_teams",
        blank=True,
    )

    # --- funding ---
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    backers = models.PositiveIntegerField(default=0)   # NEW (if you track it)

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
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        status = "✓" if self.done else "✗"
        return f"{status} {self.title}"
    # -------- Derived helpers for the front-end card shape --------
    @property
    def tags_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def days_left(self) -> int:
        if not self.end_date:
            return 0
        days = (self.end_date - timezone.now().date()).days
        return max(0, days)

    @property
    def cover_image_url(self):
        # prefer explicit cover_image, else first CampaignImage
        if self.cover_image:
            return self.cover_image
        first_image = self.images.first()
        return first_image.photo.url if first_image and first_image.photo else None

    def to_card_dict(self):
        """Return exactly what <ExploreProjectCard/> expects."""
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "school": self.school,
            "school_color_0": self.school_color_0,
            "school_color_1": self.school_color_1,
            "verified": self.verified,
            "is_sponsored": self.is_sponsored,
            "sponsored_by": self.sponsored_by,
            "cover_image": self.cover_image_url,
            "blurb": self.blurb or self.description[:180],
            "tags": self.tags_list,
            "raised": float(self.current_amount or 0),
            "goal": float(self.goal_amount or 0),
            "backers": self.backers,
            "days_left": self.days_left,
            "images": [],  # if you later expose a list
        }

    def save(self, *args, **kwargs):
        # basic auto-slug (only when creating or title changed with empty slug)
        if not self.slug:
            base = slugify(self.title)[:40] or "campaign"
            candidate = base
            idx = 2
            while Campaign.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{idx}"
                idx += 1
            self.slug = candidate
        super().save(*args, **kwargs)

class CampaignImage(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        related_name="images",
        on_delete=models.CASCADE
    )
    photo = models.ImageField(upload_to=campaign_image_upload_to)

    def __str__(self):
        return f"Image for {self.campaign.title}"
