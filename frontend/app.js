/**
 * Job Recruitment Portal Frontend - Plain Vanilla JavaScript
 * Simulates and interacts with all Django REST Framework endpoints.
 */

// Configuration
const API_BASE = window.location.origin.includes('8000') 
  ? `${window.location.origin}/api` 
  : 'http://127.0.0.1:8000/api';

// State
let currentUser = JSON.parse(localStorage.getItem('user')) || null;
let authToken = JSON.parse(localStorage.getItem('auth_tokens')) || null;
let currentApplyingJobId = null;
let currentViewingJobId = null;

// DOM Elements
const authSection = document.getElementById('auth-section');
const userSection = document.getElementById('user-section');
const userNameBadge = document.getElementById('user-name-badge');
const userRoleBadge = document.getElementById('user-role-badge');
const navEmployerTabs = document.querySelectorAll('.nav-employer-only');
const navCandidateTabs = document.querySelectorAll('.nav-candidate-only');
const apiLogsContainer = document.getElementById('api-logs');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initAuthUI();
  setupEventListeners();
  loadJobs();

  // If user was already logged in, refresh their profile
  if (authToken) {
    refreshUserProfile();
  }
});

// Setup All UI Event Listeners
function setupEventListeners() {
  // Navigation Tabs
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetTab = e.currentTarget.dataset.tab;
      switchTab(targetTab);
    });
  });

  // Auth Modals
  document.getElementById('btn-open-login').addEventListener('click', () => openModal('modal-login'));
  document.getElementById('btn-open-register').addEventListener('click', () => openModal('modal-register'));
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Modal Closers
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay || e.target.closest('.btn-close')) {
        closeAllModals();
      }
    });
  });

  // Role selector toggle on Register form
  const roleSelect = document.getElementById('reg-role');
  roleSelect.addEventListener('change', () => {
    const isEmployer = roleSelect.value === 'EMPLOYER';
    document.getElementById('reg-company-group').style.display = isEmployer ? 'flex' : 'none';
  });

  // Auth Form Submits
  document.getElementById('form-login').addEventListener('submit', handleLogin);
  document.getElementById('form-register').addEventListener('submit', handleRegister);

  // Quick Demo Buttons
  document.getElementById('btn-demo-candidate').addEventListener('click', () => quickDemoLogin('CANDIDATE'));
  document.getElementById('btn-demo-employer').addEventListener('click', () => quickDemoLogin('EMPLOYER'));

  // Job Search & Filters
  document.getElementById('filter-form').addEventListener('submit', (e) => {
    e.preventDefault();
    loadJobs();
  });
  document.getElementById('btn-reset-filters').addEventListener('click', () => {
    document.getElementById('filter-form').reset();
    loadJobs();
  });

  // Post Job Form Submit
  document.getElementById('form-post-job').addEventListener('submit', handlePostJob);

  // Application Modal Submit
  document.getElementById('form-apply-job').addEventListener('submit', handleApplyJob);

  // API Inspector Toggle
  document.getElementById('inspector-toggle').addEventListener('click', () => {
    const body = document.getElementById('inspector-body');
    const icon = document.getElementById('inspector-icon');
    body.classList.toggle('open');
    icon.textContent = body.classList.contains('open') ? '▼' : '▲';
  });
  document.getElementById('btn-clear-logs').addEventListener('click', (e) => {
    e.stopPropagation();
    apiLogsContainer.innerHTML = '<div class="empty-state" style="padding:1rem;">Logs cleared. Make API requests to see live telemetry.</div>';
  });
}

// -------------------------------------------------------------
// HTTP API Fetch Wrapper with Token Auth & Live Inspector
// -------------------------------------------------------------
async function fetchApi(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const method = options.method || 'GET';
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  // Attach JWT access token if present
  if (authToken && authToken.access) {
    headers['Authorization'] = `Bearer ${authToken.access}`;
  }

  const logId = Date.now();
  const requestPayload = options.body ? JSON.parse(options.body) : null;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    // Log to API Inspector
    logApiTraffic(method, url, response.status, requestPayload, data);

    // If 401 Unauthorized and refresh token available, attempt refresh once
    if (response.status === 401 && authToken && authToken.refresh && !options._isRetry) {
      const refreshed = await attemptTokenRefresh();
      if (refreshed) {
        options._isRetry = true;
        return fetchApi(endpoint, options);
      }
    }

    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    logApiTraffic(method, url, 'ERR', requestPayload, { error: error.message });
    throw error;
  }
}

// Log traffic in bottom inspector
function logApiTraffic(method, url, status, reqData, resData) {
  // Clear empty state if present
  const empty = apiLogsContainer.querySelector('.empty-state');
  if (empty) empty.remove();

  const statusClass = typeof status === 'number' 
    ? (status < 300 ? 'status-2xx' : (status < 500 ? 'status-4xx' : 'status-5xx')) 
    : 'status-5xx';

  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `
    <div class="log-header">
      <span class="method-badge method-${method}">${method}</span>
      <span class="status-badge ${statusClass}">${status}</span>
      <span style="color:#cbd5e1; font-weight:600;">${url.replace(API_BASE, '/api')}</span>
      <span style="color:#64748b; margin-left:auto; font-size:0.7rem;">${new Date().toLocaleTimeString()}</span>
    </div>
    ${reqData ? `<div style="color:#94a3b8;"><strong>Request:</strong> <span class="log-json">${JSON.stringify(reqData)}</span></div>` : ''}
    <div style="color:#94a3b8;"><strong>Response:</strong> <span class="log-json">${typeof resData === 'object' ? JSON.stringify(resData, null, 2) : resData}</span></div>
  `;

  apiLogsContainer.prepend(entry);
}

// Refresh expired JWT token
async function attemptTokenRefresh() {
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: authToken.refresh }),
    });
    if (res.ok) {
      const data = await res.json();
      authToken.access = data.access;
      localStorage.setItem('auth_tokens', JSON.stringify(authToken));
      return true;
    }
  } catch (err) {
    console.error('Token refresh failed:', err);
  }
  handleLogout();
  return false;
}

// -------------------------------------------------------------
// Authentication & User State
// -------------------------------------------------------------
function initAuthUI() {
  if (currentUser && authToken) {
    authSection.style.display = 'none';
    userSection.style.display = 'flex';
    userNameBadge.textContent = currentUser.username;
    userRoleBadge.textContent = currentUser.role;
    userRoleBadge.className = `role-tag ${currentUser.role.toLowerCase()}`;

    // Adjust navigation tabs visibility by role
    if (currentUser.role === 'EMPLOYER') {
      navEmployerTabs.forEach(el => el.style.display = 'inline-block');
      navCandidateTabs.forEach(el => el.style.display = 'none');
      // Prefill company name in Post Job form
      if (currentUser.company_name) {
        document.getElementById('post-company').value = currentUser.company_name;
      }
    } else {
      navEmployerTabs.forEach(el => el.style.display = 'none');
      navCandidateTabs.forEach(el => el.style.display = 'inline-block');
    }
  } else {
    authSection.style.display = 'flex';
    userSection.style.display = 'none';
    navEmployerTabs.forEach(el => el.style.display = 'none');
    navCandidateTabs.forEach(el => el.style.display = 'none');
  }
}

async function refreshUserProfile() {
  try {
    const res = await fetchApi('/auth/profile/');
    if (res.ok) {
      currentUser = res.data;
      localStorage.setItem('user', JSON.stringify(currentUser));
      initAuthUI();
    }
  } catch (err) {
    console.error('Failed to fetch profile', err);
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const res = await fetchApi('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (res.ok) {
      authToken = { access: res.data.access, refresh: res.data.refresh };
      currentUser = res.data.user;
      localStorage.setItem('auth_tokens', JSON.stringify(authToken));
      localStorage.setItem('user', JSON.stringify(currentUser));

      initAuthUI();
      closeAllModals();
      showToast(`Welcome back, ${currentUser.username}! Logged in as ${currentUser.role}.`, 'success');
      loadJobs();
    } else {
      const errorMsg = res.data.detail || res.data.non_field_errors?.[0] || 'Invalid credentials.';
      showToast(errorMsg, 'error');
    }
  } catch (err) {
    showToast('Failed to connect to backend server.', 'error');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById('reg-username').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const password2 = document.getElementById('reg-password-confirm').value;
  const role = document.getElementById('reg-role').value;
  const company_name = document.getElementById('reg-company').value.trim();
  const bio = document.getElementById('reg-bio').value.trim();

  if (password !== password2) {
    showToast('Passwords do not match!', 'warning');
    return;
  }

  const payload = {
    username,
    email,
    password,
    password2,
    role,
    company_name: role === 'EMPLOYER' ? company_name : '',
    bio,
  };

  try {
    const res = await fetchApi('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      showToast('Registration successful! Logging you in...', 'success');
      // Automatically log in
      const loginRes = await fetchApi('/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      if (loginRes.ok) {
        authToken = { access: loginRes.data.access, refresh: loginRes.data.refresh };
        currentUser = loginRes.data.user;
        localStorage.setItem('auth_tokens', JSON.stringify(authToken));
        localStorage.setItem('user', JSON.stringify(currentUser));
        initAuthUI();
        closeAllModals();
        loadJobs();
      }
    } else {
      const msg = parseApiErrors(res.data);
      showToast(msg, 'error');
    }
  } catch (err) {
    showToast('Registration failed.', 'error');
  }
}

function handleLogout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('auth_tokens');
  localStorage.removeItem('user');
  initAuthUI();
  switchTab('explore-jobs');
  showToast('Logged out successfully.', 'info');
  loadJobs();
}

// Quick Demo Login helper for 1-click evaluation
async function quickDemoLogin(role) {
  const username = role === 'EMPLOYER' ? 'demo_employer' : 'demo_candidate';
  const password = 'DemoPassword123!';

  // Attempt login first
  let loginRes = await fetchApi('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  // If user doesn't exist, create them
  if (!loginRes.ok) {
    await fetchApi('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({
        username,
        email: `${username}@example.com`,
        password,
        password2: password,
        role,
        company_name: role === 'EMPLOYER' ? 'Global Innovations Inc.' : '',
        bio: role === 'EMPLOYER' ? 'Hiring top tech talent.' : 'Full stack developer with Python experience.',
      }),
    });

    loginRes = await fetchApi('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  if (loginRes.ok) {
    authToken = { access: loginRes.data.access, refresh: loginRes.data.refresh };
    currentUser = loginRes.data.user;
    localStorage.setItem('auth_tokens', JSON.stringify(authToken));
    localStorage.setItem('user', JSON.stringify(currentUser));
    initAuthUI();
    showToast(`Quick login as ${username} (${role})!`, 'success');
    loadJobs();
    if (role === 'EMPLOYER') {
      switchTab('employer-jobs');
    } else {
      switchTab('explore-jobs');
    }
  } else {
    showToast('Failed to perform demo login.', 'error');
  }
}

// -------------------------------------------------------------
// Jobs Management (Browse, Search, Filter, Post)
// -------------------------------------------------------------
async function loadJobs() {
  const container = document.getElementById('jobs-container');
  container.innerHTML = '<div class="empty-state">Loading active job vacancies...</div>';

  const search = document.getElementById('filter-search').value.trim();
  const location = document.getElementById('filter-location').value.trim();
  const skills = document.getElementById('filter-skills').value.trim();
  const jobType = document.getElementById('filter-job-type').value;
  const minSalary = document.getElementById('filter-min-salary').value;

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (location) params.append('location', location);
  if (skills) params.append('skills', skills);
  if (jobType) params.append('job_type', jobType);
  if (minSalary) params.append('min_salary', minSalary);

  const endpoint = `/jobs/${params.toString() ? `?${params.toString()}` : ''}`;

  try {
    const res = await fetchApi(endpoint);
    if (res.ok) {
      const jobs = res.data.results || res.data;
      renderJobsList(jobs, container);
    } else {
      container.innerHTML = `<div class="empty-state">Error loading jobs: ${res.data.detail || 'Server error'}</div>`;
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state">Failed to connect to backend server. Make sure Django is running on port 8000.</div>';
  }
}

function renderJobsList(jobs, container) {
  if (!jobs || jobs.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
        <h3>No Job Postings Found</h3>
        <p>Try clearing filters or search keywords, or post a new job as an Employer.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = jobs.map(job => {
    const skillsList = (job.skills_required || '').split(',').map(s => s.trim()).filter(Boolean);
    const salaryDisplay = job.salary_min && job.salary_max
      ? `$${Number(job.salary_min).toLocaleString()} - $${Number(job.salary_max).toLocaleString()}`
      : (job.salary_min ? `From $${Number(job.salary_min).toLocaleString()}` : 'Salary not specified');

    const isCandidate = currentUser && currentUser.role === 'CANDIDATE';

    return `
      <div class="job-card">
        <div>
          <div class="job-header">
            <div>
              <h3 class="job-title">${escapeHtml(job.title)}</h3>
              <div class="company-name">🏢 ${escapeHtml(job.company_name || 'Company')}</div>
            </div>
            <span class="badge badge-blue">${job.job_type.replace('_', ' ')}</span>
          </div>

          <div class="job-badges">
            <span class="badge">📍 ${escapeHtml(job.location)}</span>
            <span class="badge">⭐ ${job.experience_level}</span>
            <span class="badge">👥 ${job.applications_count || 0} applicants</span>
          </div>

          <p class="job-desc">${escapeHtml(job.description)}</p>

          <div class="job-skills" style="margin-top:0.75rem;">
            ${skillsList.map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`).join('')}
          </div>
        </div>

        <div class="job-footer">
          <div class="salary-tag">${salaryDisplay}</div>
          ${isCandidate ? `
            <button class="btn btn-primary btn-sm" onclick="openApplyModal(${job.id}, '${escapeHtml(job.title)}', '${escapeHtml(job.company_name)}')">
              Apply Now →
            </button>
          ` : (currentUser && currentUser.role === 'EMPLOYER' ? `
            <span class="badge" style="color:#64748b;">Employer View</span>
          ` : `
            <button class="btn btn-outline-primary btn-sm" onclick="openModal('modal-login')">
              Login to Apply
            </button>
          `)}
        </div>
      </div>
    `;
  }).join('');
}

// Handle Employer Posting a new job
async function handlePostJob(e) {
  e.preventDefault();
  if (!currentUser || currentUser.role !== 'EMPLOYER') {
    showToast('Only Employers can post jobs. Please log in as an Employer.', 'error');
    return;
  }

  const payload = {
    title: document.getElementById('post-title').value.trim(),
    company_name: document.getElementById('post-company').value.trim(),
    location: document.getElementById('post-location').value.trim(),
    job_type: document.getElementById('post-job-type').value,
    experience_level: document.getElementById('post-experience').value,
    skills_required: document.getElementById('post-skills').value.trim(),
    salary_min: document.getElementById('post-salary-min').value || null,
    salary_max: document.getElementById('post-salary-max').value || null,
    description: document.getElementById('post-description').value.trim(),
    is_active: true,
  };

  try {
    const res = await fetchApi('/jobs/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      showToast('Job posted successfully!', 'success');
      document.getElementById('form-post-job').reset();
      switchTab('employer-jobs');
      loadEmployerJobs();
    } else {
      const msg = parseApiErrors(res.data);
      showToast(msg, 'error');
    }
  } catch (err) {
    showToast('Failed to post job.', 'error');
  }
}

// -------------------------------------------------------------
// Job Applications (Candidate Apply & List)
// -------------------------------------------------------------
function openApplyModal(jobId, jobTitle, companyName) {
  currentApplyingJobId = jobId;
  document.getElementById('apply-job-title').textContent = `${jobTitle} at ${companyName}`;
  document.getElementById('form-apply-job').reset();
  openModal('modal-apply');
}

async function handleApplyJob(e) {
  e.preventDefault();
  if (!currentApplyingJobId) return;

  const resume_url = document.getElementById('apply-resume-url').value.trim();
  const cover_letter = document.getElementById('apply-cover-letter').value.trim();

  if (!resume_url && !cover_letter) {
    showToast('Please provide either a Resume link or a Cover letter.', 'warning');
    return;
  }

  const payload = { resume_url, cover_letter };

  try {
    const res = await fetchApi(`/jobs/${currentApplyingJobId}/apply/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      showToast('Application submitted successfully!', 'success');
      closeAllModals();
      loadJobs();
      if (document.getElementById('tab-my-applications').classList.contains('active')) {
        loadCandidateApplications();
      }
    } else {
      // Handles duplicate application prevention message nicely
      const msg = parseApiErrors(res.data);
      showToast(msg, 'error');
    }
  } catch (err) {
    showToast('Application submission failed.', 'error');
  }
}

// Load Candidate's own applications
async function loadCandidateApplications() {
  const container = document.getElementById('candidate-applications-container');
  container.innerHTML = '<div class="empty-state">Loading your applications...</div>';

  try {
    const res = await fetchApi('/applications/my-applications/');
    if (res.ok) {
      const apps = res.data.results || res.data;
      if (!apps || apps.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            <h3>No Applications Yet</h3>
            <p>You haven't applied for any jobs yet. Browse available jobs and submit your application!</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Job Title & Company</th>
                <th>Location & Type</th>
                <th>Applied Date</th>
                <th>Resume / Notes</th>
                <th>Current Status</th>
              </tr>
            </thead>
            <tbody>
              ${apps.map(app => {
                const statusBadge = getStatusBadge(app.status);
                return `
                  <tr>
                    <td>
                      <strong>${escapeHtml(app.job_title)}</strong>
                      <div style="font-size:0.8rem; color:var(--text-muted);">${escapeHtml(app.company_name)}</div>
                    </td>
                    <td>
                      <div>📍 ${escapeHtml(app.job_location)}</div>
                      <span class="badge" style="font-size:0.7rem;">${app.job_type || 'Full Time'}</span>
                    </td>
                    <td>${new Date(app.applied_at).toLocaleDateString()}</td>
                    <td>
                      ${app.resume_url ? `<a href="${escapeHtml(app.resume_url)}" target="_blank" style="color:var(--primary); font-size:0.85rem;">View Resume ↗</a>` : '<span style="color:var(--text-muted);">No link</span>'}
                    </td>
                    <td>${statusBadge}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state">Failed to load applications.</div>';
  }
}

// -------------------------------------------------------------
// Employer Dashboard (My Jobs & Applicants Management)
// -------------------------------------------------------------
async function loadEmployerJobs() {
  const container = document.getElementById('employer-jobs-container');
  container.innerHTML = '<div class="empty-state">Loading your posted jobs...</div>';

  try {
    const res = await fetchApi('/jobs/my-jobs/');
    if (res.ok) {
      const jobs = res.data.results || res.data;
      if (!jobs || jobs.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <h3>No Jobs Posted Yet</h3>
            <p>Create your first job posting using the "Post a Job" tab.</p>
            <button class="btn btn-primary" style="margin-top:1rem;" onclick="switchTab('post-job')">Create Job Posting</button>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Job Title</th>
                <th>Location & Type</th>
                <th>Posted Date</th>
                <th>Applicants</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${jobs.map(job => `
                <tr>
                  <td>
                    <strong>${escapeHtml(job.title)}</strong>
                    <div style="font-size:0.8rem; color:var(--text-muted);">${escapeHtml(job.company_name)}</div>
                  </td>
                  <td>${escapeHtml(job.location)} (${job.job_type})</td>
                  <td>${new Date(job.created_at).toLocaleDateString()}</td>
                  <td>
                    <span class="badge badge-purple" style="font-weight:700;">${job.applications_count || 0} Candidates</span>
                  </td>
                  <td>
                    <span class="badge ${job.is_active ? 'badge-green' : 'badge-red'}">
                      ${job.is_active ? 'Active' : 'Closed'}
                    </span>
                  </td>
                  <td>
                    <div style="display:flex; gap:0.4rem;">
                      <button class="btn btn-primary btn-sm" onclick="openApplicantsModal(${job.id}, '${escapeHtml(job.title)}')">
                        👥 View Applicants (${job.applications_count || 0})
                      </button>
                      <button class="btn btn-danger btn-sm" onclick="deleteJob(${job.id})">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state">Failed to load employer jobs.</div>';
  }
}

// Open Applicants Review Modal for a specific job
async function openApplicantsModal(jobId, jobTitle) {
  currentViewingJobId = jobId;
  document.getElementById('applicants-job-title').textContent = `Applicants for: ${jobTitle}`;
  const container = document.getElementById('applicants-list-container');
  container.innerHTML = '<div class="empty-state">Loading applicants...</div>';
  openModal('modal-applicants');

  try {
    const res = await fetchApi(`/jobs/${jobId}/applicants/`);
    if (res.ok) {
      const applicants = res.data.results || res.data;
      if (!applicants || applicants.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
            <h3>No Applicants Yet</h3>
            <p>No candidates have applied for this job yet.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Contact</th>
                <th>Resume & Cover Note</th>
                <th>Status</th>
                <th>Update Status</th>
              </tr>
            </thead>
            <tbody>
              ${applicants.map(app => `
                <tr>
                  <td>
                    <strong>${escapeHtml(app.candidate_username)}</strong>
                    <div style="font-size:0.8rem; color:var(--text-muted);">${escapeHtml(app.candidate_first_name || '')} ${escapeHtml(app.candidate_last_name || '')}</div>
                  </td>
                  <td>
                    <div>✉️ ${escapeHtml(app.candidate_email || 'N/A')}</div>
                    <div style="font-size:0.8rem; color:var(--text-muted);">📞 ${escapeHtml(app.candidate_phone || 'N/A')}</div>
                  </td>
                  <td>
                    ${app.resume_url ? `<a href="${escapeHtml(app.resume_url)}" target="_blank" style="color:var(--primary); font-weight:600; font-size:0.85rem;">View Resume ↗</a>` : '<span style="color:var(--text-muted);">No URL</span>'}
                    ${app.cover_letter ? `<p style="font-size:0.8rem; color:#475569; margin-top:0.25rem; font-style:italic;">"${escapeHtml(app.cover_letter)}"</p>` : ''}
                  </td>
                  <td>${getStatusBadge(app.status)}</td>
                  <td>
                    <select onchange="updateApplicantStatus(${app.id}, this.value)" style="font-size:0.8rem; padding:0.35rem;">
                      <option value="APPLIED" ${app.status === 'APPLIED' ? 'selected' : ''}>Applied</option>
                      <option value="SHORTLISTED" ${app.status === 'SHORTLISTED' ? 'selected' : ''}>Shortlisted</option>
                      <option value="HIRED" ${app.status === 'HIRED' ? 'selected' : ''}>Hired</option>
                      <option value="REJECTED" ${app.status === 'REJECTED' ? 'selected' : ''}>Rejected</option>
                    </select>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state">Failed to load applicants.</div>';
  }
}

// Update applicant status (PATCH /api/applications/<id>/status/)
async function updateApplicantStatus(appId, newStatus) {
  try {
    const res = await fetchApi(`/applications/${appId}/status/`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus }),
    });

    if (res.ok) {
      showToast(`Status updated to ${newStatus}!`, 'success');
      // Refresh modal
      if (currentViewingJobId) {
        openApplicantsModal(currentViewingJobId, document.getElementById('applicants-job-title').textContent.replace('Applicants for: ', ''));
      }
    } else {
      showToast('Failed to update status.', 'error');
    }
  } catch (err) {
    showToast('Failed to connect.', 'error');
  }
}

// Delete Job
async function deleteJob(jobId) {
  if (!confirm('Are you sure you want to delete this job posting? This action cannot be undone.')) {
    return;
  }

  try {
    const res = await fetchApi(`/jobs/${jobId}/`, {
      method: 'DELETE',
    });

    if (res.status === 204 || res.ok) {
      showToast('Job posting deleted.', 'info');
      loadEmployerJobs();
      loadJobs();
    } else {
      showToast('Failed to delete job.', 'error');
    }
  } catch (err) {
    showToast('Failed to connect.', 'error');
  }
}

// -------------------------------------------------------------
// UI Utilities (Modals, Tabs, Toasts, Helpers)
// -------------------------------------------------------------
function switchTab(tabId) {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.toggle('active', tab.id === `tab-${tabId}`);
  });

  // Trigger data reload on tab switch
  if (tabId === 'explore-jobs') loadJobs();
  if (tabId === 'employer-jobs') loadEmployerJobs();
  if (tabId === 'my-applications') loadCandidateApplications();
}

function openModal(modalId) {
  closeAllModals();
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeAllModals() {
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.classList.remove('active');
  });
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function getStatusBadge(status) {
  switch (status) {
    case 'APPLIED':
      return `<span class="badge badge-blue">Applied</span>`;
    case 'SHORTLISTED':
      return `<span class="badge badge-purple">Shortlisted</span>`;
    case 'HIRED':
      return `<span class="badge badge-green">✓ Hired</span>`;
    case 'REJECTED':
      return `<span class="badge badge-red">Rejected</span>`;
    default:
      return `<span class="badge">${status}</span>`;
  }
}

function parseApiErrors(data) {
  if (typeof data === 'string') return data;
  if (!data) return 'An error occurred';
  if (data.detail) return data.detail;
  if (data.non_field_errors) return data.non_field_errors.join(', ');

  const errors = [];
  for (const [key, value] of Object.entries(data)) {
    const valText = Array.isArray(value) ? value.join(', ') : value;
    errors.push(`${key}: ${valText}`);
  }
  return errors.join(' | ') || 'Request failed';
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
