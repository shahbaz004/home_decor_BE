"""
Custom DRF permission classes used across the project.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Allow access only to users with ``is_staff`` flag set."""

    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsStaff(BasePermission):
    """Allow access only to users with ``is_staff`` or ``is_superuser``."""

    message = "You must be a staff member to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwner(BasePermission):
    """
    Object-level permission: allow access only to the owner of the object.
    The object must expose a ``user`` attribute.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        # Staff can always access any object.
        if request.user.is_staff:
            return True
        return obj.user == request.user


class IsOwnerOrAdmin(BasePermission):
    """Allow access to the owner or any staff member."""

    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """Read-only for everyone; write access only for admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
