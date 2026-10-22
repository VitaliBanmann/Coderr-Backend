from django.contrib import admin

from .models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Edit package details alongside their parent offer."""

    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Configure offer fields shown in the Django admin."""

    list_display = ["title", "user", "created_at", "updated_at"]
    search_fields = ["title", "description", "user__username"]
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Configure offer-package fields shown in the Django admin."""

    list_display = ["title", "offer", "offer_type", "price"]
