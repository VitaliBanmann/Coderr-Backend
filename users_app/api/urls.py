from django.urls import path

from users_app.api.views import (LoginView, ProfileListView, ProfileView,
                                 RegistrationView)

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="registration"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/<int:pk>/", ProfileView.as_view(), name="profile"),
    path(
        "profiles/business/",
        ProfileListView.as_view(),
        {"profile_type": "business"},
        name="business-profiles",
    ),
    path(
        "profiles/customer/",
        ProfileListView.as_view(),
        {"profile_type": "customer"},
        name="customer-profiles",
    ),
]
