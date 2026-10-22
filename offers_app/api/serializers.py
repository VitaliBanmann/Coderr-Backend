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
        """Allow -1 for unlimited revisions, otherwise non-negative."""
        if value < -1:
            raise serializers.ValidationError(
                "Use -1 for unlimited revisions."
            )
        return value

    def validate_features(self, value):
        """Ensure the features are a list of strings."""
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
        """Validate package types for creating or updating an offer."""
        self._validate_update_has_types(details)
        types = [
            detail["offer_type"]
            for detail in details
            if "offer_type" in detail
        ]
        self._validate_detail_types(types, details)
        return details

    def _validate_update_has_types(self, details):
        """Require an offer_type on every detail when updating."""
        if self.instance is not None and any(
            "offer_type" not in detail for detail in details
        ):
            raise serializers.ValidationError(
                "Each updated detail must include offer_type."
            )

    def _validate_detail_types(self, types, details):
        """Run the type checks that apply to creation or update."""
        self._validate_unique_types(types)
        if self.instance is None:
            self._validate_create_types(types, details)

    def _validate_unique_types(self, types):
        """Reject duplicate package types."""
        if len(types) != len(set(types)):
            raise serializers.ValidationError(
                "Each offer type must be unique."
            )

    def _validate_create_types(self, types, details):
        """Require exactly the three package types and no IDs."""
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
        """Require package details when creating an offer."""
        if self.instance is None and "details" not in attrs:
            raise serializers.ValidationError(
                {"details": "New offers must include three package details."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create the offer together with its package details."""
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
        """Update the offer and any supplied package details."""
        details = validated_data.pop("details", None)
        offer = super().update(instance, validated_data)
        if details is not None:
            self._update_details(offer, details)
        return offer

    def _update_details(self, offer, details):
        """Apply partial updates to existing packages, keeping their IDs."""
        for data in details:
            detail = self._get_existing_detail(offer, data)
            data.pop("id", None)
            for field, value in data.items():
                setattr(detail, field, value)
            detail.save()

    def _get_existing_detail(self, offer, data):
        """Return the package an update refers to or raise an error."""
        detail_id = data.get("id")
        detail = self._find_existing_detail(
            offer, detail_id, data["offer_type"]
        )
        if detail is None:
            self._raise_missing_detail_error(detail_id)
        return detail

    def _raise_missing_detail_error(self, detail_id):
        """Raise the validation error for an unknown package."""
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
        """Look up a package by ID and type, or by type alone."""
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
        """Build the absolute URL of the package."""
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
        """Return the lowest package price as a float."""
        return float(offer.min_price)

    def get_min_delivery_time(self, offer):
        """Return the shortest package delivery time in days."""
        return offer.min_delivery_time

    def get_user_details(self, offer):
        """Return the creator's name data."""
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
