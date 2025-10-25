# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from Core import settings


class UserType(models.TextChoices):
    STUDENT = "student", "Student"
    PROFESSIONAL = "professional", "Professional"

class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "phone_number"]

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    links = models.URLField(blank=True, null=True)

    # Type - Student or Professional
    user_type = models.CharField(max_length=20, choices=UserType.choices)

    # common extras
    is_email_verified = models.BooleanField(default=False)
    blurb = models.CharField(max_length=160, blank=True, null=True)
    user_score = models.IntegerField(default=0)

    def __str__(self):
        return self.email


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    school = models.CharField(max_length=255)
    major = models.CharField(max_length=255, blank=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    portfolio_url = models.URLField(blank=True)

    def __str__(self):
        return f"StudentProfile({self.user.email})"


class ProfessionalProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="professional_profile")
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    hiring = models.BooleanField(default=False)
    interests = models.CharField(max_length=255, blank=True, help_text="comma-separated areas (e.g., Product Management, Electrical Engineering)")

    def __str__(self):
        return f"ProfessionalProfile({self.user.email})"

