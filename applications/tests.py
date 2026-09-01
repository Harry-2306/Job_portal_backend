from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User
from jobs.models import Job
from .models import Application


class ApplicationsAPITests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="employer_tech",
            email="hr@tech.com",
            password="StrongPassword123!",
            role=User.Role.EMPLOYER,
            company_name="Tech Solutions"
        )
        self.other_employer = User.objects.create_user(
            username="other_hr",
            email="hr@other.com",
            password="StrongPassword123!",
            role=User.Role.EMPLOYER,
            company_name="Other Inc"
        )
        self.candidate1 = User.objects.create_user(
            username="candidate_alice",
            email="alice@example.com",
            password="StrongPassword123!",
            role=User.Role.CANDIDATE,
            first_name="Alice",
            last_name="Smith"
        )
        self.candidate2 = User.objects.create_user(
            username="candidate_charlie",
            email="charlie@example.com",
            password="StrongPassword123!",
            role=User.Role.CANDIDATE,
            first_name="Charlie",
            last_name="Brown"
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title="Full Stack Django Developer",
            company_name="Tech Solutions",
            description="Develop DRF APIs and React frontends.",
            location="Remote",
            job_type=Job.JobType.FULL_TIME,
            skills_required="Django, Python, DRF",
            is_active=True
        )

        self.other_job = Job.objects.create(
            employer=self.other_employer,
            title="Data Scientist",
            company_name="Other Inc",
            description="Machine learning and statistical modeling.",
            location="Boston",
            skills_required="Python, PyTorch",
            is_active=True
        )

        self.apply_url = reverse('job-apply', kwargs={'job_id': self.job.pk})
        self.my_applications_url = reverse('candidate-applications')
        self.employer_applications_url = reverse('employer-applications')
        self.job_applicants_url = reverse('job-applicants', kwargs={'pk': self.job.pk})

    def test_candidate_apply_job_success(self):
        self.client.force_authenticate(user=self.candidate1)
        payload = {
            "resume_url": "https://linkedin.com/in/alicesmith",
            "cover_letter": "I am passionate about Django and building APIs."
        }
        response = self.client.post(self.apply_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['application']['candidate_username'], 'candidate_alice')
        self.assertEqual(response.data['application']['status'], 'APPLIED')
        self.assertTrue(Application.objects.filter(job=self.job, candidate=self.candidate1).exists())

    def test_candidate_cannot_apply_twice_to_same_job(self):
        self.client.force_authenticate(user=self.candidate1)
        payload = {
            "resume_url": "https://linkedin.com/in/alicesmith",
            "cover_letter": "First application."
        }
        response1 = self.client.post(self.apply_url, payload, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Attempt to apply again to the same job
        response2 = self.client.post(self.apply_url, payload, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already applied", str(response2.data))

    def test_employer_cannot_apply_to_job(self):
        self.client.force_authenticate(user=self.employer)
        payload = {
            "resume_url": "https://linkedin.com/in/employer",
            "cover_letter": "I want to apply."
        }
        response = self.client.post(self.apply_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_apply(self):
        payload = {
            "resume_url": "https://linkedin.com/in/anon",
            "cover_letter": "Anon applicant"
        }
        response = self.client.post(self.apply_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_candidate_view_my_applications(self):
        Application.objects.create(
            job=self.job,
            candidate=self.candidate1,
            resume_url="https://example.com/resume1.pdf"
        )
        Application.objects.create(
            job=self.other_job,
            candidate=self.candidate1,
            resume_url="https://example.com/resume2.pdf"
        )
        self.client.force_authenticate(user=self.candidate1)
        response = self.client.get(self.my_applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_employer_view_job_applicants(self):
        Application.objects.create(
            job=self.job,
            candidate=self.candidate1,
            resume_url="https://example.com/resume1.pdf"
        )
        Application.objects.create(
            job=self.job,
            candidate=self.candidate2,
            resume_url="https://example.com/resume2.pdf"
        )

        self.client.force_authenticate(user=self.employer)
        response = self.client.get(self.job_applicants_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_other_employer_cannot_view_job_applicants(self):
        self.client.force_authenticate(user=self.other_employer)
        response = self.client.get(self.job_applicants_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employer_update_application_status(self):
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate1,
            resume_url="https://example.com/resume.pdf",
            status=Application.Status.APPLIED
        )
        status_url = reverse('application-status-update', kwargs={'pk': app.pk})

        self.client.force_authenticate(user=self.employer)
        response = self.client.patch(status_url, {'status': 'SHORTLISTED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, 'SHORTLISTED')

        # Test updating to HIRED
        response2 = self.client.patch(status_url, {'status': 'HIRED'}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, 'HIRED')

    def test_other_employer_cannot_update_application_status(self):
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate1,
            resume_url="https://example.com/resume.pdf",
            status=Application.Status.APPLIED
        )
        status_url = reverse('application-status-update', kwargs={'pk': app.pk})

        self.client.force_authenticate(user=self.other_employer)
        response = self.client.patch(status_url, {'status': 'SHORTLISTED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_candidate_cannot_update_application_status(self):
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate1,
            resume_url="https://example.com/resume.pdf",
            status=Application.Status.APPLIED
        )
        status_url = reverse('application-status-update', kwargs={'pk': app.pk})

        self.client.force_authenticate(user=self.candidate1)
        response = self.client.patch(status_url, {'status': 'HIRED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
