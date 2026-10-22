from django.db import transaction
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailWriteSerializer(serializers.ModelSerializer):
    """Validate writable fields for an offer package."""

    id = serializers.IntegerField(required=False)

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]

    def validate_revisions(self, value):
        if value < -1:
            raise serializers.ValidationError(
                "Use -1 for unlimited revisions."
            )
        return value

    def validate_features(self, value):
        if not isinstance(value, list) or not all(
            isinstance(feature, str) for feature in value
        ):
            raise serializers.ValidationError(
                "Features must be a list of strings."
            )
        return value


class OfferWriteSerializer(serializers.ModelSerializer):
    """Create and update offers with their nested package details."""

    details = OfferDetailWriteSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]
        read_only_fields = ["id"]

    def validate_details(self, details):
        if self.instance is not None and any(
            "offer_type" not in detail for detail in details
        ):
            raise serializers.ValidationError(
                "Each updated detail must include offer_type."
            )
        types = [
            detail["offer_type"]
            for detail in details
            if "offer_type" in detail
        ]
        self._validate_detail_types(types, details)
        return details

    def _validate_detail_types(self, types, details):
        self._validate_unique_types(types)
        if self.instance is None:
            self._validate_create_types(types, details)

    def _validate_unique_types(self, types):
        if len(types) != len(set(types)):
            raise serializers.ValidationError(
                "Each offer type must be unique."
            )

    def _validate_create_types(self, types, details):
        if (
            set(types) != set(OfferDetail.OfferType.values)
        ):
            raise serializers.ValidationError(
                "New offers must contain basic, standard and premium details."
            )
        if any("id" in detail for detail in details):
            raise serializers.ValidationError(
                "New offer details must not specify IDs."
            )

    def validate(self, attrs):
        if self.instance is None and "details" not in attrs:
            raise serializers.ValidationError(
                {"details": "New offers must include three package details."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        details = validated_data.pop("details")
        offer = Offer.objects.create(
            user=self.context["request"].user, **validated_data
        )
        OfferDetail.objects.bulk_create(
            [OfferDetail(offer=offer, **detail) for detail in details]
        )
        return offer

    @transaction.atomic
    def update(self, instance, validated_data):
        details = validated_data.pop("details", None)
        offer = super().update(instance, validated_data)
        if details is not None:
            self._update_details(offer, details)
        return offer

    def _update_details(self, offer, details):
        for data in details:
            detail = self._get_existing_detail(offer, data)
            data.pop("id", None)
            for field, value in data.items():
                setattr(detail, field, value)
            detail.save()

    def _get_existing_detail(self, offer, data):
        detail_id = data.get("id")
        detail = self._find_existing_detail(
            offer, detail_id, data["offer_type"]
        )
        if detail is None:
            self._raise_missing_detail_error(detail_id)
        return detail

    def _raise_missing_detail_error(self, detail_id):
        if detail_id:
            raise serializers.ValidationError(
                {
                    "details": (
                        "Detail ID and offer_type must identify an existing "
                        "detail for this offer."
                    )
                }
            )
        raise serializers.ValidationError(
            {"details": "Updates must refer to an existing offer detail."}
        )

    def _find_existing_detail(self, offer, detail_id, offer_type):
        if detail_id:
            return offer.details.filter(
                pk=detail_id, offer_type=offer_type
            ).first()
        return offer.details.filter(offer_type=offer_type).first()


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Serialize package references as API URLs."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, detail):
        return self.context["request"].build_absolute_uri(
            f"/api/offerdetails/{detail.pk}/"
        )


class OfferListSerializer(serializers.ModelSerializer):
    """Serialize offers with summary data for list and detail responses."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        ]

    def get_min_price(self, offer):
        return float(offer.min_price)

    def get_min_delivery_time(self, offer):
        return offer.min_delivery_time

    def get_user_details(self, offer):
        return {
            "first_name": offer.user.first_name,
            "last_name": offer.user.last_name,
            "username": offer.user.username,
        }


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serialize all fields of a single offer package."""

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]
