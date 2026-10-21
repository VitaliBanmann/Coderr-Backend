from django.urls import path

from orders_app.api.views import (
    BusinessOrderCountView,
    CompletedOrderCountView,
    OrderDetailView,
    OrderListCreateView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path(
        "order-count/<int:business_user_id>/",
        BusinessOrderCountView.as_view(),
        name="order-count",
    ),
    path(
        "completed-order-count/<int:business_user_id>/",
        CompletedOrderCountView.as_view(),
        name="completed-order-count",
    ),
]
