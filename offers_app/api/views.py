from decimal import Decimal, InvalidOperation

from django.db.models import Min, Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated

from offers_app.api.permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from offers_app.api.serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferWriteSerializer,
)
from offers_app.models import Offer, OfferDetail


def annotate_offer_aggregates(queryset):
    return queryset.annotate(
        min_price=Min("details__price"),
        min_delivery_time=Min("details__delivery_time_in_days"),
    )


class OfferListCreateView(generics.ListCreateAPIView):
    queryset = Offer.objects.select_related("user").prefetch_related("details")
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferWriteSerializer
        return OfferListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = annotate_offer_aggregates(super().get_queryset())
        queryset = self._apply_filters(queryset)
        ordering = (
            self.request.query_params.get("ordering") or "-updated_at"
        )
        self._validate_ordering(ordering)
        return queryset.order_by(ordering).distinct()

    def _apply_filters(self, queryset):
        params = self.request.query_params
        queryset = self._filter_creator(queryset, params)
        queryset = self._filter_min_price(queryset, params)
        queryset = self._filter_delivery_time(queryset, params)
        queryset = self._filter_search(queryset, params)
        return queryset

    def _filter_creator(self, queryset, params):
        creator_id = params.get("creator_id")
        if creator_id:
            self._validate_integer(creator_id, "creator_id")
            return queryset.filter(user_id=creator_id)
        return queryset

    def _filter_min_price(self, queryset, params):
        raw_price = params.get("min_price")
        if not raw_price:
            return queryset
        min_price = self._parse_min_price(raw_price)
        return queryset.filter(min_price__gte=min_price)

    def _parse_min_price(self, raw_price):
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
        max_delivery = params.get("max_delivery_time")
        if max_delivery:
            self._validate_integer(max_delivery, "max_delivery_time")
            return queryset.filter(min_delivery_time__lte=max_delivery)
        return queryset

    def _filter_search(self, queryset, params):
        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        return queryset

    def _validate_ordering(self, ordering):
        allowed = {"updated_at", "-updated_at", "min_price", "-min_price"}
        if ordering not in allowed:
            raise ValidationError({"ordering": "Use updated_at or min_price."})

    def _validate_integer(self, value, field):
        try:
            if int(value) < 0:
                raise ValueError
        except ValueError as error:
            raise ValidationError(
                {field: "Enter a non-negative integer."}
            ) from error


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.select_related("user").prefetch_related("details")
    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return annotate_offer_aggregates(super().get_queryset())

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OfferListSerializer
        return OfferWriteSerializer


class OfferPackageDetailView(generics.RetrieveAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
