# campaigns/services.py
from django.utils import timezone
from .models import Campaign

def recompute_trending_scores():
    now = timezone.now()
    qs = Campaign.objects.filter(is_active=True).only(
        "id", "last_activity_at", "like_count", "view_count",
        "comment_count", "donation_sum_24h", "recruiter_saves", "backer_count_24h"
    )

    for c in qs:
        hours = max(1.0, (now - c.last_activity_at).total_seconds() / 3600.0)

        score = (
            3  * (c.like_count or 0) +
            1  * (c.view_count or 0) +
            6  * (c.comment_count or 0) +
            8  * float(c.donation_sum_24h or 0) +
            10 * (c.recruiter_saves or 0) +
            12 * (c.backer_count_24h or 0)
        ) / (1 + 0.15 * hours)

        # Optional: clamp to avoid extremes
        c.trending_score = max(0.0, float(score))
        c.save(update_fields=["trending_score"])
