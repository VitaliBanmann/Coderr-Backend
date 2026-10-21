from django.urls import path

from offers_app.api.views import (
    OfferDetailView,
    OfferListCreateView,
    OfferPackageDetailView,
)

urlpatterns = [
    path("offers/", OfferListCreateView.as_view(), name="offers"),
    path("offers/<int:pk>/", OfferDetailView.as_view(), name="offer-detail"),
    path(
        "offerdetails/<int:pk>/",
        OfferPackageDetailView.as_view(),
        name="offer-package-detail",
    ),
]
