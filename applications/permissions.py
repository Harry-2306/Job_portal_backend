from rest_framework import permissions
from accounts.models import User


class IsApplicationJobEmployer(permissions.BasePermission):
    """
    Permission allowing only the employer who posted the job to view or update its applications.
    """
    message = "Only the employer who posted this job can manage this application."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.EMPLOYER
        )

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            obj.job.employer == request.user
        )


class IsApplicationCandidate(permissions.BasePermission):
    """
    Permission allowing only the candidate who submitted the application to view it.
    """
    message = "You do not have permission to view this application."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.CANDIDATE
        )

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            obj.candidate == request.user
        )


class IsApplicationParty(permissions.BasePermission):
    """
    Permission allowing either the candidate or the job's employer to access the application.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return bool(
            obj.candidate == request.user or
            obj.job.employer == request.user
        )
