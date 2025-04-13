from django.contrib import admin
from .models import Campaign

# Register your models here.


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "goal_amount", "current_amount", "creator", "start_date", "created_at")
    search_fields = ("title", "description", "creator__username")
    list_filter = ("start_date", "created_at")