import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    company_name = django_filters.CharFilter(field_name='company_name', lookup_expr='icontains')
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    skills = django_filters.CharFilter(field_name='skills_required', lookup_expr='icontains')
    job_type = django_filters.ChoiceFilter(choices=Job.JobType.choices)
    experience_level = django_filters.ChoiceFilter(choices=Job.ExperienceLevel.choices)
    min_salary = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    max_salary = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = Job
        fields = [
            'title',
            'company_name',
            'location',
            'skills',
            'job_type',
            'experience_level',
            'min_salary',
            'max_salary',
            'is_active',
        ]
