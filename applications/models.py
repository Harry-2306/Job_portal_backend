from django.db import models
from django.conf import settings
from jobs.models import Job


class Application(models.Model):
    """
    Job Application model tracking candidate submissions and hiring statuses.
    """
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        REJECTED = 'REJECTED', 'Rejected'
        HIRED = 'HIRED', 'Hired'

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    resume_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to online resume, portfolio, or LinkedIn profile."
    )
    resume_file = models.FileField(
        upload_to='resumes/%Y/%m/',
        blank=True,
        null=True,
        help_text="Uploaded resume document (PDF/DOCX)."
    )
    cover_letter = models.TextField(
        blank=True,
        null=True,
        help_text="Candidate cover letter or introduction."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
        help_text="Application lifecycle status."
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'candidate'],
                name='unique_candidate_job_application'
            )
        ]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['applied_at']),
        ]

    def __str__(self):
        return f"{self.candidate.username} -> {self.job.title} ({self.get_status_display()})"
