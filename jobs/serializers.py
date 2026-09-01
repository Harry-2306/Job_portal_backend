from rest_framework import serializers
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    employer_id = serializers.ReadOnlyField(source='employer.id')
    employer_username = serializers.ReadOnlyField(source='employer.username')
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id',
            'employer_id',
            'employer_username',
            'title',
            'company_name',
            'description',
            'location',
            'job_type',
            'experience_level',
            'skills_required',
            'salary_min',
            'salary_max',
            'is_active',
            'applications_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'employer_id', 'employer_username', 'applications_count', 'created_at', 'updated_at']

    def get_applications_count(self, obj):
        return obj.applications.count()

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')

        # Fallback to existing instance values on partial update
        if self.instance:
            if salary_min is None:
                salary_min = self.instance.salary_min
            if salary_max is None:
                salary_max = self.instance.salary_max

        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                raise serializers.ValidationError({
                    "salary_max": "Maximum salary cannot be less than minimum salary."
                })

        return attrs

    def create(self, validated_data):
        employer = self.context['request'].user
        if not validated_data.get('company_name'):
            validated_data['company_name'] = employer.company_name or employer.username
        return Job.objects.create(employer=employer, **validated_data)
