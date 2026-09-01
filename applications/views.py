from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from accounts.permissions import IsCandidate, IsEmployer
from jobs.models import Job
from .models import Application
from .permissions import IsApplicationJobEmployer, IsApplicationCandidate, IsApplicationParty
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationDetailSerializer,
    ApplicationStatusUpdateSerializer,
)


class ApplyJobView(generics.CreateAPIView):
    """
    API endpoint for Candidates to apply for a specific job posting.
    """
    serializer_class = ApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def create(self, request, *args, **kwargs):
        job_id = self.kwargs.get('job_id')
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            raise NotFound("Job not found.")

        # Prepare request data with the job id
        data = request.data.copy()
        data['job'] = job.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        detail_data = ApplicationDetailSerializer(application, context={'request': request}).data
        return Response(
            {
                "message": "Application submitted successfully.",
                "application": detail_data,
            },
            status=status.HTTP_201_CREATED
        )


class CandidateApplicationsListView(generics.ListAPIView):
    """
    API endpoint for Candidates to view all jobs they have applied for.
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['applied_at', 'status']
    ordering = ['-applied_at']

    def get_queryset(self):
        return Application.objects.select_related('job', 'candidate').filter(candidate=self.request.user)


class EmployerApplicationsListView(generics.ListAPIView):
    """
    API endpoint for Employers to view all applications received across all their posted jobs.
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['job', 'status']
    ordering_fields = ['applied_at', 'status']
    ordering = ['-applied_at']

    def get_queryset(self):
        return Application.objects.select_related('job', 'candidate').filter(
            job__employer=self.request.user
        )


class ApplicationDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve detailed information about a single application.
    Accessible only by the Candidate applicant or the Employer who owns the job.
    """
    queryset = Application.objects.select_related('job', 'candidate').all()
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsApplicationParty]


class ApplicationStatusUpdateView(generics.UpdateAPIView):
    """
    API endpoint for Employers to update the status of an applicant (Applied, Shortlisted, Rejected, Hired).
    """
    queryset = Application.objects.select_related('job', 'candidate').all()
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsApplicationJobEmployer]
    http_method_names = ['patch', 'put']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        detail_data = ApplicationDetailSerializer(instance, context={'request': request}).data
        return Response(
            {
                "message": f"Application status updated to '{instance.status}'.",
                "application": detail_data,
            },
            status=status.HTTP_200_OK
        )
