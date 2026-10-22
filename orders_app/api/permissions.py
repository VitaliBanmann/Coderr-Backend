from rest_framework.permissions import BasePermission


class IsBusinessOrderOwner(BasePermission):
    """Allow status updates by the business user who owns the order."""

    def has_object_permission(self, request, view, order):
        """Check that the user is the business user of the order."""
        return (
            request.user.is_authenticated
            and request.user.type == "business"
            and order.business_user_id == request.user.pk
        )


class IsCustomer(BasePermission):
    """Allow requests from authenticated customer users."""

    def has_permission(self, request, view):
        """Check that the user is authenticated and a customer."""
        return (
            request.user.is_authenticated
            and request.user.type == "customer"
        )


class IsOrderParticipant(BasePermission):
    """Allow access to users listed on the order."""

    def has_object_permission(self, request, view, order):
        """Check that the user is the customer or business of the order."""
        return request.user.pk in {
            order.customer_user_id,
            order.business_user_id,
        }
