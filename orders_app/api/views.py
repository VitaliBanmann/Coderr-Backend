from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders_app.api.permissions import (
    IsBusinessOrderOwner,
    IsCustomer,
    IsOrderParticipant,
)
from orders_app.api.serializers import (
    CreateOrderSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)
from orders_app.models import Order
from users_app.models import User


class OrderListCreateView(generics.ListCreateAPIView):
    """List a user's orders and let customers place new orders."""

    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        """Use the creation serializer for POST, otherwise the read one."""
        if self.request.method == "POST":
            return CreateOrderSerializer
        return OrderSerializer

    def get_permissions(self):
        """Require a customer for POST in addition to authentication."""
        permissions = [IsAuthenticated()]
        if self.request.method == "POST":
            permissions.append(IsCustomer())
        return permissions

    def get_queryset(self):
        """Return only orders the requesting user takes part in."""
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        ).select_related("customer_user", "business_user")

    def create(self, request):
        """Create an order and respond with its full representation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return self._created_response(order)

    def _created_response(self, order):
        """Build the 201 response for a newly created order."""
        data = OrderSerializer(order).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an order according to user permissions."""

    queryset = Order.objects.select_related("customer_user", "business_user")
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """Choose permissions per HTTP method."""
        if self.request.method == "DELETE":
            return [IsAdminUser()]
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsBusinessOrderOwner()]
        return [IsAuthenticated(), IsOrderParticipant()]

    def get_serializer_class(self):
        """Use the status serializer for PATCH, otherwise the full one."""
        if self.request.method == "PATCH":
            return OrderStatusSerializer
        return OrderSerializer


class BusinessOrderCountView(APIView):
    """Return the number of orders in the configured status for a business."""

    permission_classes = [IsAuthenticated]
    response_key = "order_count"
    order_status = Order.Status.IN_PROGRESS

    def get(self, _request, business_user_id):
        """Count the business user's orders in the configured status."""
        business_user = get_object_or_404(
            User, pk=business_user_id, type=User.BUSINESS
        )
        count = Order.objects.filter(
            business_user=business_user,
            status=self.order_status,
        ).aggregate(count=Count("id"))["count"]
        return Response({self.response_key: count})


class CompletedOrderCountView(BusinessOrderCountView):
    """Return the completed-order count for a business."""

    response_key = "completed_order_count"
    order_status = Order.Status.COMPLETED
