from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from reviews_app.api.permissions import IsCustomer, IsReviewAuthorOrReadOnly
from reviews_app.api.serializers import ReviewSerializer
from reviews_app.models import Review


class ReviewListCreateView(generics.ListCreateAPIView):
    """List reviews and allow eligible customers to create one."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.select_related("business_user", "reviewer")
    pagination_class = None

    def get_queryset(self):
        """Return the filtered and ordered review queryset."""
        queryset = self._apply_filters(super().get_queryset())
        return self._apply_ordering(queryset)

    def _apply_filters(self, queryset):
        """Validate the ID parameters and filter by them."""
        params = self.request.query_params
        self._validate_filter_id(params, "business_user_id")
        self._validate_filter_id(params, "reviewer_id")
        return self._filter_reviewers(queryset, params)

    def _apply_ordering(self, queryset):
        """Order the queryset by the validated ordering parameter."""
        ordering = self.request.query_params.get("ordering", "-updated_at")
        if ordering not in {"updated_at", "-updated_at", "rating", "-rating"}:
            raise ValidationError({"ordering": "Use updated_at or rating."})
        return queryset.order_by(ordering)

    def _filter_reviewers(self, queryset, params):
        """Filter reviews by business user and reviewer."""
        if params.get("business_user_id"):
            queryset = queryset.filter(
                business_user_id=params["business_user_id"]
            )
        if params.get("reviewer_id"):
            queryset = queryset.filter(reviewer_id=params["reviewer_id"])
        return queryset

    def _validate_filter_id(self, params, field):
        """Ensure an ID query parameter contains only digits."""
        value = params.get(field)
        if value and not value.isdecimal():
            raise ValidationError({field: "Enter a valid user ID."})

    def get_permissions(self):
        """Require a customer for POST in addition to authentication."""
        permissions = [IsAuthenticated()]
        if self.request.method == "POST":
            permissions.append(IsCustomer())
        return permissions

    def perform_create(self, serializer):
        """Store the requesting user as the review author."""
        serializer.save(reviewer=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a review according to author permissions."""

    queryset = Review.objects.select_related("business_user", "reviewer")
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewAuthorOrReadOnly]
    http_method_names = ["get", "patch", "delete", "head", "options"]
