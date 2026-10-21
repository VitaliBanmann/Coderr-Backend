from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsBusinessUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.type == "business"
        )


class IsOfferOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, offer):
        return (
            request.method in SAFE_METHODS
            or offer.user_id == request.user.pk
        )
