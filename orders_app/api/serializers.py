from django.db import transaction
from rest_framework import serializers

from offers_app.models import OfferDetail
from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
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
    offer_detail_id = serializers.IntegerField()

    def validate_offer_detail_id(self, value):
        if not OfferDetail.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Offer detail not found.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        detail = OfferDetail.objects.select_related("offer__user").get(
            pk=validated_data["offer_detail_id"]
        )
        return Order.objects.create(
            customer_user=self.context["request"].user,
            business_user=detail.offer.user,
            **self._package_snapshot(detail),
        )

    def _package_snapshot(self, detail):
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
    class Meta:
        model = Order
        fields = ["status"]
