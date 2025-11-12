# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from Core import settings
from typing import Optional, Literal
from pydantic import BaseModel, AnyUrl


class UserType(models.TextChoices):
    STUDENT = "student", "Student"
    PROFESSIONAL = "professional", "Professional"
    GUEST = "guest", "Guest"

class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username" , "first_name", "last_name",]

    username = models.CharField(max_length=80, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    # Type - Student or Professional
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.STUDENT,)

    # common extras
    is_email_verified = models.BooleanField(default=False)
    blurb = models.CharField(max_length=160, blank=True, null=True)
    user_score = models.IntegerField(default=0)

    profile_image = models.ImageField(
        upload_to="students/profilepics/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.email

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    school = models.CharField(max_length=255)
    school_color_0 = models.CharField(max_length=7, blank=True, null=True)  # Hex color code
    school_color_1 = models.CharField(max_length=7, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    active_project_count = models.PositiveIntegerField(default=0)
    total_funds_raised = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    co_creator_count = models.PositiveIntegerField(default=0)


    def __str__(self):
        return f"{self.user.username} - Student"

class ProfessionalProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="professional_profile")
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    hiring = models.BooleanField(default=False)
    interests = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"{self.user.username} - Professional"

class StudentIn(BaseModel):
    school: str
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    portfolio_url: Optional[AnyUrl] = None

class ProfessionalIn(BaseModel):
    company: str
    title: Optional[str] = None
    linkedin_url: Optional[AnyUrl] = None
    hiring: Optional[bool] = None
    interests: Optional[str] = None

class RegisterUser(BaseModel):
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None

    user_type: Literal["student", "professional"]
    bio: Optional[str] = None
    wallet_address: Optional[str] = None
    link: Optional[AnyUrl] = None

    student: Optional[StudentIn] = None
    professional: Optional[ProfessionalIn] = None