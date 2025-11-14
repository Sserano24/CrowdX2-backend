# campaigns/services.py
import datetime
from django.utils import timezone
from .models import Campaign


def recompute_trending_scores():
    """
    Recompute trending scores for active campaigns.

    Score is based on:
      - like_count
      - view_count
      - comment_count
      - donation_sum
      - recruiter_saves

    We also flip the `trending` flag:
      - trending = True if score increased by >= 100 since last run
      - trending = False otherwise

    NOTE: This assumes the task runs roughly once per day,
    so the previous `trending_score` is treated as "score about a day ago".
    """
    qs = Campaign.objects.filter(is_active=True).only(
        "id",
        "like_count",
        "view_count",
        "comment_count",
        "donation_sum",      # make sure this field exists; rename if needed
        "recruiter_saves",
        "trending_score",
        "trending",
    )

    for c in qs:
        # Defensive defaults
        likes = c.like_count or 0
        views = c.view_count or 0
        comments = c.comment_count or 0
        donations = float(c.donation_sum or 0.0)
        saves = c.recruiter_saves or 0

        # You can tweak these weights as you like
        score = (
            3 * likes +
            1 * views +
            5 * comments +
            10 * donations +
            8 * saves
        )

        previous_score = float(c.trending_score or 0.0)
        delta = score - previous_score

        # Trending logic:
        # - If score jumped by >= 100 since last run -> trending
        # - Otherwise -> not trending
        is_trending = delta >= 100.0

        # Only hit the DB if something changed
        fields_to_update = []
        if score != previous_score:
            c.trending_score = score
            fields_to_update.append("trending_score")
        if c.trending != is_trending:
            c.trending = is_trending
            fields_to_update.append("trending")

        if fields_to_update:
            c.save(update_fields=fields_to_update)
