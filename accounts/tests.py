from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.candidate_data = {
            "username": "candidate_john",
            "email": "john@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "role": "CANDIDATE",
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Experienced Python developer"
        }
        self.employer_data = {
            "username": "tech_employer",
            "email": "hr@techcorp.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "role": "EMPLOYER",
            "company_name": "Tech Corp Inc.",
            "phone_number": "+1234567890",
            "bio": "Leading tech company"
        }
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.profile_url = reverse('auth-profile')
        self.refresh_url = reverse('auth-token-refresh')

    def test_candidate_registration(self):
        response = self.client.post(self.register_url, self.candidate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'candidate_john')
        self.assertEqual(response.data['user']['role'], 'CANDIDATE')
        self.assertTrue(User.objects.filter(username='candidate_john').exists())

    def test_employer_registration(self):
        response = self.client.post(self.register_url, self.employer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'tech_employer')
        self.assertEqual(response.data['user']['role'], 'EMPLOYER')
        self.assertEqual(response.data['user']['company_name'], 'Tech Corp Inc.')

    def test_registration_password_mismatch(self):
        data = self.candidate_data.copy()
        data['password2'] = 'MismatchPassword123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_duplicate_email(self):
        self.client.post(self.register_url, self.candidate_data, format='json')
        duplicate_data = self.candidate_data.copy()
        duplicate_data['username'] = 'another_user'
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_jwt_login_success(self):
        # Register user first
        self.client.post(self.register_url, self.candidate_data, format='json')

        # Attempt login
        login_payload = {
            "username": "candidate_john",
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'CANDIDATE')

    def test_jwt_login_invalid_credentials(self):
        self.client.post(self.register_url, self.candidate_data, format='json')
        login_payload = {
            "username": "candidate_john",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_refresh(self):
        self.client.post(self.register_url, self.candidate_data, format='json')
        login_res = self.client.post(self.login_url, {
            "username": "candidate_john",
            "password": "StrongPassword123!"
        }, format='json')
        refresh_token = login_res.data['refresh']

        response = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_profile_authenticated(self):
        user = User.objects.create_user(
            username="candidate_jane",
            email="jane@example.com",
            password="StrongPassword123!",
            role="CANDIDATE"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'candidate_jane')
        self.assertEqual(response.data['role'], 'CANDIDATE')

    def test_user_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
