from rest_framework.permissions import BasePermission


class IsBusinessOrderOwner(BasePermission):
    """Allow status updates by the business user who owns the order."""

    def has_object_permission(self, request, view, order):
        return (
            request.user.is_authenticated
            and request.user.type == "business"
            and order.business_user_id == request.user.pk
        )


class IsCustomer(BasePermission):
    """Allow requests from authenticated customer users."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.type == "customer"
        )


class IsOrderParticipant(BasePermission):
    """Allow access to users listed on the order."""

    def has_object_permission(self, request, view, order):
        return request.user.pk in {
            order.customer_user_id,
            order.business_user_id,
        }
