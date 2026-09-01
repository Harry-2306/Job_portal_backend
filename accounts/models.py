from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model supporting two user types: Employer and Candidate.
    """
    class Role(models.TextChoices):
        EMPLOYER = 'EMPLOYER', 'Employer'
        CANDIDATE = 'CANDIDATE', 'Candidate'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CANDIDATE,
        help_text="Designates whether the user is an Employer or a Candidate."
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Company name (for Employers)."
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone number."
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Brief professional summary or company overview."
    )

    @property
    def is_employer(self) -> bool:
        return self.role == self.Role.EMPLOYER

    @property
    def is_candidate(self) -> bool:
        return self.role == self.Role.CANDIDATE

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
