# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class Role(models.TextChoices):
    CREATOR = "creator", "Creator"
    EXPLORER = "explorer", "Explorer"

class User(AbstractUser):
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone_number' ]
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    links = models.URLField(blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EXPLORER,   # default to explorer if you want
    )

    #new
    is_email_verified = models.BooleanField(default=False)
    school = models.CharField(max_length=255, blank=True, null=True)
    blurb = models.CharField(max_length=160, blank=True, null=True)
    user_score = models.IntegerField(default=0)


    @property
    def associated_campaigns(self):

        from campaigns.models import Campaign  # local import to avoid circulars
        return (
            Campaign.objects
            .filter(Q(creator=self) | Q(team_members=self))
            .values("id", "title")
            .distinct()
        )

    def __str__(self):
        return self.email

