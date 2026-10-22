from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProfileOwnerOrReadOnly(BasePermission):
    """Allow safe profile reads or changes made by the profile owner."""

    def has_object_permission(self, request, view, user):
        return request.method in SAFE_METHODS or user.pk == request.user.pk
