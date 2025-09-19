# campaigns/tasks.py
from celery import shared_task
from .services import recompute_trending_scores

@shared_task
def recompute_trending_scores_task():
    recompute_trending_scores()
