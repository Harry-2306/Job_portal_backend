"""
Main URL Configuration for Job Recruitment API.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    Job Recruitment API Root endpoint with navigation links.
    """
    return Response({
        "message": "Welcome to the Job Recruitment API",
        "documentation": {
            "auth": {
                "register": request.build_absolute_uri('/api/auth/register/'),
                "login": request.build_absolute_uri('/api/auth/login/'),
                "refresh_token": request.build_absolute_uri('/api/auth/token/refresh/'),
                "profile": request.build_absolute_uri('/api/auth/profile/'),
            },
            "jobs": {
                "list_and_create": request.build_absolute_uri('/api/jobs/'),
                "my_jobs": request.build_absolute_uri('/api/jobs/my-jobs/'),
            },
            "applications": {
                "my_applications": request.build_absolute_uri('/api/applications/my-applications/'),
                "employer_applications": request.build_absolute_uri('/api/applications/employer-applications/'),
            }
        }
    })


urlpatterns = [
    # Interactive Frontend
    path('', TemplateView.as_view(template_name='index.html'), name='frontend'),
    path('portal/', TemplateView.as_view(template_name='index.html'), name='frontend-portal'),

    # API Root & Apps
    path('api/', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/applications/', include('applications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
