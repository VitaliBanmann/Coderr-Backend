from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users_app.api.permissions import IsProfileOwnerOrReadOnly
from users_app.api.serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileSerializer,
    RegistrationSerializer,
)
from users_app.models import User


def token_payload(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.pk,
    }


class RegistrationView(generics.CreateAPIView):
    """Register a user and return an authentication token."""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        user = self._create_user(request.data)
        return Response(
            token_payload(user),
            status=status.HTTP_201_CREATED,
        )

    def _create_user(self, data):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class LoginView(APIView):
    """Authenticate a user and return an authentication token."""

    permission_classes = [AllowAny]

    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return self._invalid_credentials()
        return Response(token_payload(user))

    def _invalid_credentials(self):
        return Response(
            {"non_field_errors": ["Invalid username or password."]},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve a profile and allow its owner to update it."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsProfileOwnerOrReadOnly]
    queryset = User.objects.all()
    lookup_field = "pk"


class ProfileListView(generics.ListAPIView):
    """List profiles filtered by the requested user type."""

    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.kwargs["profile_type"] == User.BUSINESS:
            return BusinessProfileListSerializer
        return CustomerProfileListSerializer

    def get_queryset(self):
        return User.objects.filter(type=self.kwargs["profile_type"])
