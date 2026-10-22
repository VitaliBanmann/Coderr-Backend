from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Configure order fields shown in the Django admin."""

    list_display = [
        "title",
        "customer_user",
        "business_user",
        "status",
        "created_at",
    ]
    list_filter = ["status"]
