from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CoderrUserAdmin(UserAdmin):
    """Add Coderr profile fields to the Django user admin."""

    fieldsets = UserAdmin.fieldsets + (
        (
            "Coderr profile",
            {
                "fields": (
                    "type",
                    "location",
                    "tel",
                    "description",
                    "working_hours",
                    "profile_image",
                )
            },
        ),
    )
    list_display = ["username", "email", "type", "is_staff"]
