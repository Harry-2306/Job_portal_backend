from django.db import models
from django.conf import settings


class Job(models.Model):
    """
    Job model representing a vacancy posted by an Employer.
    """
    class JobType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full-time'
        PART_TIME = 'PART_TIME', 'Part-time'
        CONTRACT = 'CONTRACT', 'Contract'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        REMOTE = 'REMOTE', 'Remote'

    class ExperienceLevel(models.TextChoices):
        ENTRY = 'ENTRY', 'Entry Level'
        MID = 'MID', 'Mid Level'
        SENIOR = 'SENIOR', 'Senior Level'
        LEAD = 'LEAD', 'Lead / Executive'

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs'
    )
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    job_type = models.CharField(
        max_length=30,
        choices=JobType.choices,
        default=JobType.FULL_TIME
    )
    experience_level = models.CharField(
        max_length=30,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID
    )
    skills_required = models.CharField(
        max_length=500,
        help_text="Comma-separated skills (e.g. Python, Django, PostgreSQL, REST APIs)"
    )
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum salary"
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum salary"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this job posting is active and accepting applications."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['location']),
            models.Index(fields=['job_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company_name}"
