from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.api_views import BaseInfoView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("users_app.api.urls")),
    path("api/", include("offers_app.api.urls")),
    path("api/", include("orders_app.api.urls")),
    path("api/", include("reviews_app.api.urls")),
    path(
        "api/base-info/",
        BaseInfoView.as_view(),
        name="base-info",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
