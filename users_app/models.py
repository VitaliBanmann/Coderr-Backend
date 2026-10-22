from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A Coderr account with customer or business profile fields."""

    CUSTOMER = "customer"
    BUSINESS = "business"
    USER_TYPES = [(CUSTOMER, "Customer"), (BUSINESS, "Business")]

    type = models.CharField(
        max_length=10, choices=USER_TYPES, default=CUSTOMER
    )
    location = models.CharField(max_length=255, blank=True)
    tel = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    working_hours = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(
        upload_to="profiles/", blank=True, null=True
    )

    class Meta:
        ordering = ["username"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        """Return the username."""
        return self.username
