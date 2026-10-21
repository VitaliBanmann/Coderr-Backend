from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsReviewAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, review):
        return (
            request.method in SAFE_METHODS
            or review.reviewer_id == request.user.pk
        )


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.type == "customer"
        )
