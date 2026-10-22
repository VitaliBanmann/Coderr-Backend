from decimal import Decimal, InvalidOperation

from django.db.models import Min, Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated

from offers_app.api.permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from offers_app.api.serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferWriteSerializer,
)
from offers_app.models import Offer, OfferDetail


def annotate_offer_aggregates(queryset):
    """Annotate offers with their lowest price and shortest delivery time."""
    return queryset.annotate(
        min_price=Min("details__price"),
        min_delivery_time=Min("details__delivery_time_in_days"),
    )


class OfferPagination(PageNumberPagination):
    """Limit offer lists to a configurable number of results per page."""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100


class OfferListCreateView(generics.ListCreateAPIView):
    """List public offers and allow business users to create offers."""

    queryset = Offer.objects.select_related("user").prefetch_related("details")
    pagination_class = OfferPagination

    def get_serializer_class(self):
        """Use the write serializer for creation, otherwise the list one."""
        if self.request.method == "POST":
            return OfferWriteSerializer
        return OfferListSerializer

    def get_permissions(self):
        """Require a business user for POST; allow public reads."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [AllowAny()]

    def get_queryset(self):
        """Return the annotated, filtered, and ordered offer queryset."""
        queryset = annotate_offer_aggregates(super().get_queryset())
        queryset = self._apply_filters(queryset)
        return self._apply_ordering(queryset).distinct()

    def _apply_ordering(self, queryset):
        """Order the queryset by the validated ordering parameter."""
        ordering = (
            self.request.query_params.get("ordering") or "-updated_at"
        )
        self._validate_ordering(ordering)
        return queryset.order_by(ordering)

    def _apply_filters(self, queryset):
        """Apply all supported query-parameter filters."""
        params = self.request.query_params
        queryset = self._filter_creator(queryset, params)
        queryset = self._filter_min_price(queryset, params)
        queryset = self._filter_delivery_time(queryset, params)
        queryset = self._filter_search(queryset, params)
        return queryset

    def _filter_creator(self, queryset, params):
        """Filter offers by the creator's user ID."""
        creator_id = params.get("creator_id")
        if creator_id:
            self._validate_integer(creator_id, "creator_id")
            return queryset.filter(user_id=creator_id)
        return queryset

    def _filter_min_price(self, queryset, params):
        """Filter offers by their lowest package price."""
        raw_price = params.get("min_price")
        if not raw_price:
            return queryset
        min_price = self._parse_min_price(raw_price)
        return queryset.filter(min_price__gte=min_price)

    def _parse_min_price(self, raw_price):
        """Convert the price parameter to a non-negative Decimal."""
        try:
            min_price = Decimal(raw_price)
        except InvalidOperation as error:
            raise ValidationError(
                {"min_price": "Enter a valid price."}
            ) from error
        if not min_price.is_finite() or min_price < 0:
            raise ValidationError({"min_price": "Price cannot be negative."})
        return min_price

    def _filter_delivery_time(self, queryset, params):
        """Filter offers by their shortest delivery time."""
        max_delivery = params.get("max_delivery_time")
        if max_delivery:
            self._validate_integer(max_delivery, "max_delivery_time")
            return queryset.filter(min_delivery_time__lte=max_delivery)
        return queryset

    def _filter_search(self, queryset, params):
        """Search offer titles and descriptions."""
        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        return queryset

    def _validate_ordering(self, ordering):
        """Reject ordering values that the API does not support."""
        allowed = {"updated_at", "-updated_at", "min_price", "-min_price"}
        if ordering not in allowed:
            raise ValidationError({"ordering": "Use updated_at or min_price."})

    def _validate_integer(self, value, field):
        """Ensure a query parameter is a non-negative integer."""
        try:
            if int(value) < 0:
                raise ValueError
        except ValueError as error:
            raise ValidationError(
                {field: "Enter a non-negative integer."}
            ) from error


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an offer owned by the requester."""

    queryset = Offer.objects.select_related("user").prefetch_related("details")
    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Return offers annotated with price and delivery aggregates."""
        return annotate_offer_aggregates(super().get_queryset())

    def get_serializer_class(self):
        """Use the read serializer for GET, otherwise the write one."""
        if self.request.method == "GET":
            return OfferListSerializer
        return OfferWriteSerializer


class OfferPackageDetailView(generics.RetrieveAPIView):
    """Retrieve one offer package for an authenticated user."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
