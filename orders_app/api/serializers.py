from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from offers_app.models import OfferDetail
from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Serialize complete order records."""

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    """Create an order from an existing offer package."""

    offer_detail_id = serializers.IntegerField()

    def validate_offer_detail_id(self, value):
        """Ensure the referenced offer package exists."""
        if not OfferDetail.objects.filter(pk=value).exists():
            raise NotFound("Offer detail not found.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create an order that snapshots the selected offer package."""
        detail = OfferDetail.objects.select_related("offer__user").get(
            pk=validated_data["offer_detail_id"]
        )
        return Order.objects.create(
            customer_user=self.context["request"].user,
            business_user=detail.offer.user,
            **self._package_snapshot(detail),
        )

    def _package_snapshot(self, detail):
        """Copy the order-relevant package fields into a dictionary."""
        fields = [
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]
        return {field: getattr(detail, field) for field in fields}


class OrderStatusSerializer(serializers.ModelSerializer):
    """Allow updates only to an order's status."""

    class Meta:
        model = Order
        fields = OrderSerializer.Meta.fields
        read_only_fields = [
            field for field in OrderSerializer.Meta.fields if field != "status"
        ]

    def validate(self, attrs):
        """Reject input fields other than the order status."""
        unexpected_fields = set(self.initial_data) - {"status"}
        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "Only the status field can be updated."
                    for field in sorted(unexpected_fields)
                }
            )
        return attrs
