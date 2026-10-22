from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Configure review fields shown in the Django admin."""

    list_display = ["business_user", "reviewer", "rating", "updated_at"]
    list_filter = ["rating"]
