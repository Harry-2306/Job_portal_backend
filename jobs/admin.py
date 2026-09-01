from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company_name', 'employer', 'location', 'job_type', 'is_active', 'created_at']
    list_filter = ['job_type', 'experience_level', 'is_active', 'created_at']
    search_fields = ['title', 'company_name', 'location', 'skills_required', 'description']
