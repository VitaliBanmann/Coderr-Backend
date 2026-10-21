from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from reviews_app.api.permissions import IsCustomer, IsReviewAuthorOrReadOnly
from reviews_app.api.serializers import ReviewSerializer
from reviews_app.models import Review


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.select_related("business_user", "reviewer")
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        self._validate_filter_id(params, "business_user_id")
        self._validate_filter_id(params, "reviewer_id")
        queryset = self._filter_reviewers(queryset, params)
        ordering = params.get("ordering", "-updated_at")
        if ordering not in {"updated_at", "-updated_at", "rating", "-rating"}:
            raise ValidationError({"ordering": "Use updated_at or rating."})
        return queryset.order_by(ordering)

    def _filter_reviewers(self, queryset, params):
        if params.get("business_user_id"):
            queryset = queryset.filter(
                business_user_id=params["business_user_id"]
            )
        if params.get("reviewer_id"):
            queryset = queryset.filter(reviewer_id=params["reviewer_id"])
        return queryset

    def _validate_filter_id(self, params, field):
        value = params.get(field)
        if value and not value.isdecimal():
            raise ValidationError({field: "Enter a valid user ID."})

    def get_permissions(self):
        permissions = [IsAuthenticated()]
        if self.request.method == "POST":
            permissions.append(IsCustomer())
        return permissions

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related("business_user", "reviewer")
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewAuthorOrReadOnly]
    http_method_names = ["get", "patch", "delete", "head", "options"]
