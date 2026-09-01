from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import IsEmployer
from .models import Job
from .filters import JobFilter
from .serializers import JobSerializer
from .permissions import IsJobOwner, IsJobOwnerOrReadOnly


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing job postings:
    - Public / Candidates: List & search active jobs, retrieve job details.
    - Employers: Create, update, and delete their own job postings, view their posted jobs and applicants.
    """
    queryset = Job.objects.select_related('employer').all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'company_name', 'location', 'skills_required', 'description']
    ordering_fields = ['created_at', 'salary_min', 'salary_max', 'title']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsEmployer]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsJobOwner]
        elif self.action in ['my_jobs', 'applicants']:
            permission_classes = [permissions.IsAuthenticated, IsEmployer]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        # For public list view, default to active jobs unless query parameter specifies otherwise
        if self.action == 'list':
            if 'is_active' not in self.request.query_params:
                queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=False, methods=['get'], url_path='my-jobs')
    def my_jobs(self, request):
        """
        List all jobs posted by the currently authenticated employer.
        """
        jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='applicants')
    def applicants(self, request, pk=None):
        """
        List all applicants/applications for a specific job posted by the current employer.
        """
        job = self.get_object()
        if job.employer != request.user:
            return Response(
                {"detail": "You do not have permission to view applicants for this job."},
                status=status.HTTP_403_FORBIDDEN
            )

        from applications.serializers import ApplicationDetailSerializer
        applications = job.applications.select_related('candidate', 'job').all().order_by('-applied_at')
        page = self.paginate_queryset(applications)
        if page is not None:
            serializer = ApplicationDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ApplicationDetailSerializer(applications, many=True)
        return Response(serializer.data)
