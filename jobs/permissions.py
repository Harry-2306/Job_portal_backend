from rest_framework import permissions
from accounts.models import User


class IsEmployerOrReadOnly(permissions.BasePermission):
    """
    Allow read-only requests to anyone; allow job creation only to employers.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.EMPLOYER
        )


class IsJobOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission allowing only the employer who created the job to modify or delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            obj.employer == request.user
        )


class IsJobOwner(permissions.BasePermission):
    """
    Permission allowing only the employer who created the job to access specific job management endpoints.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.EMPLOYER
        )

    def has_object_permission(self, request, view, obj):
        employer = getattr(obj, 'employer', None)
        if employer is None and hasattr(obj, 'job'):
            employer = obj.job.employer
        return bool(
            request.user and
            request.user.is_authenticated and
            employer == request.user
        )
