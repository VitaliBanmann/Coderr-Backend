from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsBusinessUser(BasePermission):
    """Allow requests from authenticated business users."""

    def has_permission(self, request, view):
        """Check that the user is authenticated and a business user."""
        return (
            request.user.is_authenticated
            and request.user.type == "business"
        )


class IsOfferOwnerOrReadOnly(BasePermission):
    """Allow safe reads or writes by the offer owner."""

    def has_object_permission(self, request, view, offer):
        """Allow read access to everyone and write access to the owner."""
        return (
            request.method in SAFE_METHODS
            or offer.user_id == request.user.pk
        )
