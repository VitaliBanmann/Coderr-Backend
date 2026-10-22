from django.conf import settings
from django.db import models


class Offer(models.Model):
    """A service offer published by a business user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "offer"
        verbose_name_plural = "offers"

    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    """A priced package belonging to an offer."""

    class OfferType(models.TextChoices):
        """The supported package tiers."""

        BASIC = "basic", "Basic"
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details"
    )
    title = models.CharField(max_length=200)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=10, choices=OfferType.choices)

    class Meta:
        ordering = ["id"]
        verbose_name = "offer detail"
        verbose_name_plural = "offer details"
        constraints = [
            models.UniqueConstraint(
                fields=["offer", "offer_type"],
                name="unique_offer_detail_type",
            )
        ]

    def __str__(self):
        return f"{self.offer.title} ({self.offer_type})"
