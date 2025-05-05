# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    links = models.URLField(blank=True, null=True)

