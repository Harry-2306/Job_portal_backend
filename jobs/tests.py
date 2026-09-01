from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User
from .models import Job


class JobsAPITests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="employer_corp",
            email="employer@corp.com",
            password="StrongPassword123!",
            role=User.Role.EMPLOYER,
            company_name="Acme Corp"
        )
        self.other_employer = User.objects.create_user(
            username="other_employer",
            email="other@corp.com",
            password="StrongPassword123!",
            role=User.Role.EMPLOYER,
            company_name="Other Corp"
        )
        self.candidate = User.objects.create_user(
            username="candidate_bob",
            email="bob@example.com",
            password="StrongPassword123!",
            role=User.Role.CANDIDATE
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title="Senior Backend Engineer",
            company_name="Acme Corp",
            description="Build scalable REST APIs with Django and Python.",
            location="Remote",
            job_type=Job.JobType.FULL_TIME,
            experience_level=Job.ExperienceLevel.SENIOR,
            skills_required="Python, Django, PostgreSQL, Docker",
            salary_min=120000,
            salary_max=160000,
            is_active=True
        )

        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Frontend React Developer",
            company_name="Acme Corp",
            description="Build modern user interfaces.",
            location="New York",
            job_type=Job.JobType.CONTRACT,
            experience_level=Job.ExperienceLevel.MID,
            skills_required="React, TypeScript, CSS",
            salary_min=90000,
            salary_max=110000,
            is_active=True
        )

        self.list_url = reverse('job-list')
        self.detail_url = reverse('job-detail', kwargs={'pk': self.job.pk})
        self.my_jobs_url = reverse('job-my-jobs')

    def test_list_jobs_public(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_job_detail_public(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Senior Backend Engineer")
        self.assertEqual(response.data['employer_username'], "employer_corp")

    def test_employer_create_job_success(self):
        self.client.force_authenticate(user=self.employer)
        payload = {
            "title": "DevOps Engineer",
            "company_name": "Acme Corp",
            "description": "Maintain CI/CD and cloud infra.",
            "location": "San Francisco",
            "job_type": "FULL_TIME",
            "experience_level": "MID",
            "skills_required": "Kubernetes, AWS, Terraform",
            "salary_min": 130000,
            "salary_max": 150000,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "DevOps Engineer")
        self.assertEqual(response.data['employer_id'], self.employer.id)

    def test_candidate_cannot_create_job(self):
        self.client.force_authenticate(user=self.candidate)
        payload = {
            "title": "Software Engineer",
            "description": "Invalid creation attempt",
            "location": "Remote",
            "skills_required": "Python",
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_job(self):
        payload = {
            "title": "Software Engineer",
            "description": "Invalid creation attempt",
            "location": "Remote",
            "skills_required": "Python",
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employer_update_own_job(self):
        self.client.force_authenticate(user=self.employer)
        payload = {"title": "Lead Backend Engineer"}
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Lead Backend Engineer")

    def test_other_employer_cannot_update_job(self):
        self.client.force_authenticate(user=self.other_employer)
        payload = {"title": "Hacked Title"}
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employer_delete_own_job(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())

    def test_filter_jobs_by_skills(self):
        response = self.client.get(f"{self.list_url}?skills=Django")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Senior Backend Engineer")

    def test_filter_jobs_by_location(self):
        response = self.client.get(f"{self.list_url}?location=New+York")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Frontend React Developer")

    def test_filter_jobs_by_job_type(self):
        response = self.client.get(f"{self.list_url}?job_type=CONTRACT")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['job_type'], "CONTRACT")

    def test_search_jobs_general_query(self):
        response = self.client.get(f"{self.list_url}?search=React")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Frontend React Developer")

    def test_employer_my_jobs_endpoint(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.get(self.my_jobs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
