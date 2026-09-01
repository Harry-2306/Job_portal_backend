from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet
from applications.views import ApplyJobView

router = DefaultRouter()
router.register(r'', JobViewSet, basename='job')

urlpatterns = [
    path('<int:job_id>/apply/', ApplyJobView.as_view(), name='job-apply'),
    path('', include(router.urls)),
]
