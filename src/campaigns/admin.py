from django.contrib import admin
from django.utils.html import format_html
from .models import Campaign, CampaignImage,CampaignMilestone


class CampaignImageInline(admin.TabularInline):  # or admin.StackedInline
    model = CampaignImage
    extra = 1                      # show one empty upload row by default
    fields = ("photo", "thumbnail")
    readonly_fields = ("thumbnail",)

    def thumbnail(self, obj):
        if getattr(obj, "photo", None) and hasattr(obj.photo, "url"):
            return format_html('<img src="{}" style="height:80px;border-radius:6px;" />', obj.photo.url)
        return "—"
    thumbnail.short_description = "Preview"

class CampaignMilestoneInline(admin.TabularInline):
    model = CampaignMilestone
    extra = 1
    fields = ("title", "summary", "done")
    show_change_link = True


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "goal_amount_formatted",
        "current_amount_formatted",
        "creator",
        "start_date",
        "created_at",
    )
    search_fields = ("title", "description", "creator__username")
    list_filter = ("start_date", "created_at")
    inlines = [CampaignImageInline]   # ← show images on the Campaign page

    def goal_amount_formatted(self, obj):
        return f"${obj.goal_amount:.2f}"
    goal_amount_formatted.short_description = "Goal Amount"

    def current_amount_formatted(self, obj):
        return f"${obj.current_amount:.2f}"
    current_amount_formatted.short_description = "Amount Raised"


# Optional: direct access to images in the admin sidebar
@admin.register(CampaignImage)
class CampaignImageAdmin(admin.ModelAdmin):
    list_display = ("id", "campaign", "preview_small")
    readonly_fields = ("preview_small",)
    search_fields = ("campaign__title",)

    def preview_small(self, obj):
        if getattr(obj, "photo", None) and hasattr(obj.photo, "url"):
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.photo.url)
        return "—"
    preview_small.short_description = "Preview"
