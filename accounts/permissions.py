from rest_framework import permissions
from .models import User


class IsEmployer(permissions.BasePermission):
    """
    Permission check allowing only authenticated users with the 'EMPLOYER' role.
    """
    message = "Only employers have permission to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.EMPLOYER
        )


class IsCandidate(permissions.BasePermission):
    """
    Permission check allowing only authenticated users with the 'CANDIDATE' role.
    """
    message = "Only candidates have permission to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.CANDIDATE
        )
