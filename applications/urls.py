from django.urls import path
from .views import (
    CandidateApplicationsListView,
    EmployerApplicationsListView,
    ApplicationDetailView,
    ApplicationStatusUpdateView,
)

urlpatterns = [
    path('my-applications/', CandidateApplicationsListView.as_view(), name='candidate-applications'),
    path('employer-applications/', EmployerApplicationsListView.as_view(), name='employer-applications'),
    path('<int:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),
]
