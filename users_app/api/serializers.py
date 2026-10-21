from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from users_app.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "repeated_password",
            "type",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password": error.messages}
            ) from error
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source="pk", read_only=True)
    created_at = serializers.DateTimeField(
        source="date_joined", read_only=True
    )
    file = serializers.ImageField(
        source="profile_image", required=False, allow_null=True
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    tel = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    working_hours = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]
        read_only_fields = ["username", "type", "created_at"]
