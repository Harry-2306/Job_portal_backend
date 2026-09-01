from rest_framework import serializers
from accounts.models import User
from jobs.models import Job
from .models import Application


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used by Candidates to apply for a job.
    """
    class Meta:
        model = Application
        fields = [
            'id',
            'job',
            'resume_url',
            'resume_file',
            'cover_letter',
            'status',
            'applied_at',
        ]
        read_only_fields = ['id', 'status', 'applied_at']

    def validate(self, attrs):
        request = self.context.get('request')
        candidate = request.user
        job = attrs.get('job')

        if not candidate.is_authenticated:
            raise serializers.ValidationError("Authentication is required to apply for jobs.")

        if candidate.role != User.Role.CANDIDATE:
            raise serializers.ValidationError("Only candidates can apply for jobs.")

        if job and not job.is_active:
            raise serializers.ValidationError("This job posting is currently closed and not accepting applications.")

        # Check duplicate application
        if job and Application.objects.filter(job=job, candidate=candidate).exists():
            raise serializers.ValidationError("You have already applied for this job.")

        resume_url = attrs.get('resume_url')
        resume_file = attrs.get('resume_file')
        cover_letter = attrs.get('cover_letter')

        if not resume_url and not resume_file and not cover_letter:
            raise serializers.ValidationError(
                "Please provide a resume URL, resume file, or a cover letter."
            )

        return attrs

    def create(self, validated_data):
        candidate = self.context['request'].user
        return Application.objects.create(candidate=candidate, **validated_data)


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer providing rich information about an application for candidates & employers.
    """
    job_id = serializers.ReadOnlyField(source='job.id')
    job_title = serializers.ReadOnlyField(source='job.title')
    company_name = serializers.ReadOnlyField(source='job.company_name')
    job_location = serializers.ReadOnlyField(source='job.location')
    job_type = serializers.ReadOnlyField(source='job.job_type')

    candidate_id = serializers.ReadOnlyField(source='candidate.id')
    candidate_username = serializers.ReadOnlyField(source='candidate.username')
    candidate_email = serializers.ReadOnlyField(source='candidate.email')
    candidate_first_name = serializers.ReadOnlyField(source='candidate.first_name')
    candidate_last_name = serializers.ReadOnlyField(source='candidate.last_name')
    candidate_phone = serializers.ReadOnlyField(source='candidate.phone_number')

    class Meta:
        model = Application
        fields = [
            'id',
            'job_id',
            'job_title',
            'company_name',
            'job_location',
            'job_type',
            'candidate_id',
            'candidate_username',
            'candidate_email',
            'candidate_first_name',
            'candidate_last_name',
            'candidate_phone',
            'resume_url',
            'resume_file',
            'cover_letter',
            'status',
            'applied_at',
            'updated_at',
        ]
        read_only_fields = fields


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used by Employers to update applicant status (Applied, Shortlisted, Rejected, Hired).
    """
    class Meta:
        model = Application
        fields = ['status']

    def validate_status(self, value):
        if value not in Application.Status.values:
            raise serializers.ValidationError(
                f"Invalid status '{value}'. Allowed options: {Application.Status.values}"
            )
        return value
