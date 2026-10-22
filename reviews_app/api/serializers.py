from rest_framework import serializers

from reviews_app.models import Review
from users_app.models import User


class ReviewSerializer(serializers.ModelSerializer):
    """Validate and serialize customer reviews."""

    reviewer = serializers.PrimaryKeyRelatedField(read_only=True)
    business_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(type=User.BUSINESS),
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reviewer", "created_at", "updated_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

    def validate(self, attrs):
        if self.instance is not None and "business_user" in attrs:
            self._raise_immutable_business_error()
        if self.instance is None:
            self._validate_single_review(attrs)
        return attrs

    def _raise_immutable_business_error(self):
        raise serializers.ValidationError(
            {"business_user": "The reviewed business cannot be changed."}
        )

    def _validate_single_review(self, attrs):
        exists = Review.objects.filter(
            business_user=attrs["business_user"],
            reviewer=self.context["request"].user,
        ).exists()
        if exists:
            raise serializers.ValidationError(
                {"business_user": "You have already reviewed this business."}
            )
