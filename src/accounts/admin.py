# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, UserType, StudentProfile, ProfessionalProfile


# ---- Inlines ---------------------------------------------------------------

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    fk_name = "user"
    extra = 0
    can_delete = False
    fields = ("school","school_color_0","school_color_1", "major", "graduation_year", "gpa", "linkedin", "github", "active_project_count", "total_funds_raised", "co_creator_count")


class ProfessionalProfileInline(admin.StackedInline):
    model = ProfessionalProfile
    fk_name = "user"
    extra = 0
    can_delete = False
    fields = ("company", "title", "linkedin", "hiring", "interests")


# ---- User Admin ------------------------------------------------------------

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display  = ("email", "username", "user_type", "is_active", "is_staff")
    list_filter   = ("user_type", "is_active", "is_staff", "is_superuser", "is_email_verified")
    search_fields = ("email", "username", "first_name", "last_name", "phone_number")
    ordering      = ("email",)
    readonly_fields = ("last_login", "date_joined")

    # Common fields available to all on the change page
    base_fieldsets = (
        ("Account", {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "bio", "link")}),
        ("Status & Access", {"fields": ("is_email_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    # Student-only fields you want editable on the User form
    student_fieldsets = (
        ("User Type", {"fields": ("user_type",)}),
        ("Student extras", {"fields": ("wallet_address", "blurb", "user_score")}),
    )

    # Professional-only fields you want editable on the User form
    professional_fieldsets = (
        ("User Type", {"fields": ("user_type",)}),
        ("Professional extras", {"fields": ("wallet_address", "blurb", "user_score")}),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Show different field groups depending on the selected user's type.
        On the add page (obj is None), show a minimal set where user_type can be chosen.
        """
        if obj is None:
            # Add form: show common + a small type group, extras come after save
            return (
                ("Account", {"fields": ("email", "username", "password")}),
                ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "bio", "link")}),
                ("User Type", {"fields": ("user_type",)}),
                ("Status & Access", {"fields": ("is_email_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
            )

        # Change form: branch on type
        if obj.user_type == UserType.STUDENT:
            return self.base_fieldsets[:2] + self.student_fieldsets + self.base_fieldsets[2:]
        if obj.user_type == UserType.PROFESSIONAL:
            return self.base_fieldsets[:2] + self.professional_fieldsets + self.base_fieldsets[2:]
        # Default / unknown: just show base
        return self.base_fieldsets

    def get_inlines(self, request, obj=None):
        """
        Only show the matching profile inline for the current user's type.
        """
        if obj is None:
            return []
        if obj.user_type == UserType.STUDENT:
            return [StudentProfileInline]
        if obj.user_type == UserType.PROFESSIONAL:
            return [ProfessionalProfileInline]
        return []

    def save_model(self, request, obj, form, change):
        """
        Ensure the related profile exists after saving so the inline is visible next load.
        """
        super().save_model(request, obj, form, change)
        if obj.user_type == UserType.STUDENT:
            StudentProfile.objects.get_or_create(user=obj)
        elif obj.user_type == UserType.PROFESSIONAL:
            ProfessionalProfile.objects.get_or_create(user=obj)
