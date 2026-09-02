# Job Recruitment REST API & Interactive Simulator (Django + DRF + Plain Vanilla JS)

A production-ready Job Recruitment REST API built with **Django**, **Django REST Framework (DRF)**, **SimpleJWT**, and an **Interactive Frontend Simulator** built with plain **HTML5, CSS, and Vanilla JavaScript**.

---

## Key Features

- **Interactive Frontend UI**:
  - Browse, search, and filter job postings with instant updates.
  - Role-based views for **Candidate** and **Employer**.
  - 1-Click Demo Mode (Instant switch between Candidate & Employer profiles).
  - Apply for jobs with resume links and cover notes.
  - Employer applicant review dashboard with live status updates (`Applied`, `Shortlisted`, `Hired`, `Rejected`).
  - **Live API Telemetry & Response Inspector** docked at the bottom showing exact REST requests and responses in real time.
- **JWT Authentication**: Secure user registration and login issuing JSON Web Tokens (access & refresh).
- **Role-Based Access Control (RBAC)**:
  - **Employer**: Post jobs, update/delete own jobs, view applicants for posted jobs, and update application statuses.
  - **Candidate**: Browse and search active jobs, submit applications, and track application statuses.
- **Duplicate Prevention**: Database constraints and serializer validation prevent candidates from applying to the same job multiple times.
- **Search & Filtering**: Search jobs by title, skills, description, company name, location, and filter by job type, experience level, and salary range.
- **PostgreSQL Ready**: Configured for PostgreSQL with automatic fallback to SQLite for local development.
- **Automated Test Suite**: 32 comprehensive tests covering authentication, RBAC permissions, job CRUD, filtering, applications, and status workflows.

---

## Tech Stack

- **Backend**: Python 3.11+, Django 5.x, Django REST Framework
- **Authentication**: SimpleJWT (`djangorestframework-simplejwt`)
- **Filtering**: `django-filter`
- **CORS**: `django-cors-headers`
- **Database**: PostgreSQL / SQLite
- **Frontend**: Plain HTML5, Modern CSS (custom properties, responsive grid/flexbox), Vanilla JavaScript (ES6+ `fetch` API)

---

## Project Structure

```text
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── frontend/                # Interactive Plain HTML/CSS/JS Frontend
│   ├── index.html           # Single-page UI
│   ├── style.css            # Modern responsive CSS design
│   └── app.js               # Client-side state & API communication
├── templates/
│   └── index.html           # Django template integration
├── config/                  # Django project configuration
│   ├── settings.py          # DRF, SimpleJWT, DB & app configuration
│   ├── urls.py              # Root routing & frontend serving
│   └── wsgi.py
├── accounts/                # User management & authentication
│   ├── models.py            # Custom User model (role: EMPLOYER | CANDIDATE)
│   ├── permissions.py       # IsEmployer, IsCandidate
│   ├── serializers.py       # RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer
│   ├── urls.py
│   ├── views.py
│   └── tests.py             # Auth & profile test cases
├── jobs/                    # Job postings & search
│   ├── models.py            # Job model
│   ├── filters.py           # JobFilter (title, location, skills, salary, job_type)
│   ├── permissions.py       # IsJobOwner, IsJobOwnerOrReadOnly
│   ├── serializers.py       # JobSerializer
│   ├── urls.py
│   ├── views.py             # JobViewSet with custom actions
│   └── tests.py             # Job CRUD, permission, and search tests
└── applications/            # Job application workflow
    ├── models.py            # Application model with unique constraint & status choices
    ├── permissions.py       # IsApplicationJobEmployer, IsApplicationCandidate
    ├── serializers.py       # ApplicationCreateSerializer, ApplicationDetailSerializer, ApplicationStatusUpdateSerializer
    ├── urls.py
    ├── views.py             # ApplyJobView, CandidateApplicationsListView, EmployerApplicationsListView, ApplicationStatusUpdateView
    └── tests.py             # Application submission, duplicate prevention, and status update tests
```

---

## Setup & Running the Application

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables (Optional)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

> **Note**: Defaults to SQLite out-of-the-box if no PostgreSQL credentials are provided.

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Start the Development Server

```bash
python manage.py runserver
```

### 5. Access the Interactive Frontend & APIs

- **Interactive Web App**: Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in any browser.
- **REST API Directory**: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Using the Frontend Simulator

1. **Quick Evaluation**:
   - Click **`👤 Candidate Mode`** in the top hero bar to instantly log in as a candidate, browse jobs, search by skill/salary, and submit an application.
   - Click **`🏢 Employer Mode`** to instantly log in as an employer, publish new jobs, and review/shortlist/hire applicants.
2. **Testing Duplicate Application Prevention**:
   - As a Candidate, apply for a job once.
   - Attempt to click "Apply Now" on the same job again.
   - Notice the API responds with `400 Bad Request` and displays: *"You have already applied for this job."*
3. **Live API Telemetry**:
   - Open the **"Live DRF API Telemetry & Response Inspector"** at the bottom of the screen to inspect every HTTP request method, URL, headers, and JSON response payload in real time.

---

## Running Automated Tests

Run the complete test suite (32 tests):

```bash
python manage.py test
```

---

## API Documentation & Endpoints

### Base URL: `http://127.0.0.1:8000/api/`

All authenticated endpoints require the `Authorization` header with a Bearer token:
```http
Authorization: Bearer <access_token>
```

---

### 1. Authentication Endpoints (`/api/auth/`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register a new user (`EMPLOYER` or `CANDIDATE`) | Public |
| `POST` | `/api/auth/login/` | Obtain JWT access and refresh tokens | Public |
| `POST` | `/api/auth/token/refresh/` | Refresh expired access token | Public |
| `GET` | `/api/auth/profile/` | Retrieve current user profile | Authenticated |
| `PUT/PATCH` | `/api/auth/profile/` | Update current user profile | Authenticated |

#### Register Employer Example
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "techcorp_hr",
  "email": "hr@techcorp.com",
  "password": "SecurePassword123!",
  "password2": "SecurePassword123!",
  "role": "EMPLOYER",
  "company_name": "Tech Corp Inc.",
  "phone_number": "+1-555-0199",
  "bio": "Leading cloud solutions provider."
}
```

#### Register Candidate Example
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "john_dev",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "password2": "SecurePassword123!",
  "role": "CANDIDATE",
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Full-stack Django & React developer."
}
```

#### Login Example
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "john_dev",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi...",
  "user": {
    "id": 1,
    "username": "john_dev",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "CANDIDATE",
    "company_name": null
  }
}
```

---

### 2. Job Endpoints (`/api/jobs/`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/jobs/` | List all active jobs (supports search & filters) | Public |
| `POST` | `/api/jobs/` | Create a new job posting | Employer Only |
| `GET` | `/api/jobs/<id>/` | Retrieve job details | Public |
| `PUT/PATCH` | `/api/jobs/<id>/` | Update job posting | Job Owner Employer |
| `DELETE` | `/api/jobs/<id>/` | Delete job posting | Job Owner Employer |
| `GET` | `/api/jobs/my-jobs/` | List all jobs posted by the logged-in employer | Employer Only |
| `GET` | `/api/jobs/<id>/applicants/` | List all applicants for a specific job | Job Owner Employer |

#### Create Job (Employer Only)
```http
POST /api/jobs/
Authorization: Bearer <employer_access_token>
Content-Type: application/json

{
  "title": "Senior Python/Django Developer",
  "company_name": "Tech Corp Inc.",
  "description": "We are seeking an experienced Django backend developer to build high-scale APIs.",
  "location": "Remote",
  "job_type": "FULL_TIME",
  "experience_level": "SENIOR",
  "skills_required": "Python, Django, Django REST Framework, PostgreSQL, Docker",
  "salary_min": 120000.00,
  "salary_max": 160000.00,
  "is_active": true
}
```

#### Search & Filter Jobs
```http
GET /api/jobs/?search=Django
GET /api/jobs/?skills=PostgreSQL
GET /api/jobs/?location=Remote
GET /api/jobs/?job_type=FULL_TIME
GET /api/jobs/?min_salary=100000&max_salary=150000
GET /api/jobs/?ordering=-salary_max
```

---

### 3. Application Endpoints (`/api/applications/` & `/api/jobs/<id>/apply/`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/jobs/<job_id>/apply/` | Apply for a job | Candidate Only |
| `GET` | `/api/applications/my-applications/` | List all applications submitted by candidate | Candidate Only |
| `GET` | `/api/applications/employer-applications/` | List all applications received across all jobs | Employer Only |
| `GET` | `/api/applications/<id>/` | View application details | Applicant or Job Employer |
| `PATCH` | `/api/applications/<id>/status/` | Update application status | Job Owner Employer |

#### Apply for a Job (Candidate Only)
```http
POST /api/jobs/1/apply/
Authorization: Bearer <candidate_access_token>
Content-Type: application/json

{
  "resume_url": "https://linkedin.com/in/johndoe",
  "cover_letter": "I have 5+ years of experience building scalable backend services with Django."
}
```

#### Update Application Status (Employer Only)
```http
PATCH /api/applications/1/status/
Authorization: Bearer <employer_access_token>
Content-Type: application/json

{
  "status": "SHORTLISTED"
}
```
*Allowed status values*: `APPLIED`, `SHORTLISTED`, `REJECTED`, `HIRED`

---

