CampusServe — Backend API

CampusServe is a University Maintenance Service Request Management System.
 This repository contains the Django REST Framework backend API that powers the application.

---

## 🌐 Live URLs

| Resource | URL |
|---|---|
| **Backend API Base** | https://campusserve-backend-production.up.railway.app/api/ |
| **Swagger UI (API Docs)** | https://campusserve-backend-production.up.railway.app/api/schema/swagger-ui/ |
| **ReDoc** | https://campusserve-backend-production.up.railway.app/api/schema/redoc/ |
| **Django Admin** | https://campusserve-backend-production.up.railway.app/admin/ |
| **Frontend App** | https://campusserve-frontend.vercel.app |

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Academic Context](#academic-context)

---

## About the Project

CampusServe replaces fragmented, manual maintenance request handling
(phone calls, paper forms, WhatsApp) with a centralised digital platform.
The backend provides:

- **JWT-based authentication** with access and refresh tokens
- **Role-based access control** for students/staff, maintenance officers, and administrators
- **Full CRUD** on service requests with status machine validation
- **File/image upload** for fault evidence (stored on Cloudinary)
- **In-app notifications** auto-generated on status changes and assignments
- **CSV data export** for administrators
- **Complete audit trail** on every status transition
- **OpenAPI 3.0 documentation** via Swagger UI

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11.9 | Runtime |
| Django | 5.0.1 | Web framework |
| Django REST Framework | 3.14.0 | REST API layer |
| djangorestframework-simplejwt | 5.4+ | JWT authentication |
| drf-spectacular | 0.27.x | OpenAPI 3.0 schema + Swagger UI |
| django-cors-headers | 4.3.x | CORS configuration |
| django-filter | 23.5 | Queryset filtering |
| Pillow | 10.2.x | Image processing |
| Cloudinary + django-cloudinary-storage | latest | Media file storage CDN |
| psycopg2-binary | 2.9.x | PostgreSQL driver |
| python-decouple | 3.8 | Environment variable management |
| Gunicorn | 21.2.x | Production WSGI server |
| WhiteNoise | 6.6.x | Static file serving |
| dj-database-url | latest | DATABASE_URL parsing |
| pytest-django | 4.7.x | Testing framework |

---

## Features

### Advanced Features Implemented (7 of minimum 4 required)

| # | Feature | Description |
|---|---|---|
| 1 | **JWT Authentication** | Access token (24h) + Refresh token (7d) + Blacklisting on logout |
| 2 | **Role-Based Access Control** | Custom permission classes: `IsAdmin`, `IsMaintenanceOfficer`, `IsAdminOrOfficer` |
| 3 | **File/Image Upload** | Evidence images uploaded to Cloudinary CDN via Django `ImageField` |
| 4 | **Search, Filter & Pagination** | DRF `SearchFilter`, `DjangoFilterBackend`, `PageNumberPagination` (10/page) |
| 5 | **Audit Trail / Activity Log** | `StatusUpdateLog` records every status transition immutably |
| 6 | **CSV Data Export** | Admin-only streaming CSV endpoint with all request fields |
| 7 | **In-App Notifications** | Auto-created on submission, assignment, and status change events |

---

## API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Register new student/staff account |
| POST | `/api/auth/login/` | No | Login — returns access + refresh + user |
| POST | `/api/auth/refresh/` | No | Exchange refresh token for new access token |

### Users
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/users/me/` | Yes | Get authenticated user profile |
| GET | `/api/users/` | Admin | List all users (search + filter + pagination) |
| PATCH | `/api/users/{id}/toggle_active/` | Admin | Activate / deactivate a user |
| GET | `/api/users/maintenance_officers/` | Yes | List all active maintenance officers |
| GET | `/api/users/stats/` | Admin | User counts by role |

### Service Requests
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/requests/` | Yes | List requests (role-scoped, paginated) |
| POST | `/api/requests/` | Student/Staff | Submit a new service request |
| GET | `/api/requests/{id}/` | Yes | Get specific request with full detail |
| POST | `/api/requests/{id}/assign/` | Admin | Assign request to an officer |
| POST | `/api/requests/{id}/update_status/` | Admin/Officer | Update status (state machine validated) |
| GET | `/api/requests/stats/` | Yes | Aggregated statistics (role-scoped) |
| GET | `/api/requests/export_csv/` | Admin | Download all requests as CSV |

### Categories & Notifications
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/categories/` | Yes | List all active request categories |
| GET | `/api/notifications/` | Yes | List notifications for authenticated user |
| POST | `/api/notifications/mark_all_read/` | Yes | Mark all notifications as read |
| GET | `/api/notifications/unread_count/` | Yes | Get unread notification count |

---

## Database Schema

### Entities

```
roles                  → id, name (student/staff/maintenance_officer/admin), description
users                  → id (UUID), email, first_name, last_name, role_id (FK), is_active
request_categories     → id, name, icon, is_active
service_requests       → id (UUID), reference_number, title, description, category_id,
                         requester_id, location, building, room_number, priority,
                         status, evidence_image, created_at, updated_at
assignments            → id (UUID), service_request_id (OneToOne), officer_id,
                         assigned_by_id, notes, expected_completion_date
status_update_logs     → id (UUID), service_request_id, updated_by_id,
                         old_status, new_status, comment, created_at
notifications          → id (UUID), user_id, title, message, notification_type,
                         is_read, reference_id, created_at
```

### Status Machine

```
pending → assigned → in_progress → completed
        ↓              ↓
     rejected       rejected
```

---

## Project Structure

```
campusserve-backend/
├── campusserve/
│   ├── settings/
│   │   ├── __init__.py        # Auto-selects dev or prod settings
│   │   ├── base.py            # Shared: INSTALLED_APPS, JWT, Cloudinary, DRF
│   │   ├── development.py     # SQLite, DEBUG=True
│   │   └── production.py      # PostgreSQL from PG env vars
│   ├── urls.py                # Root URL conf + Swagger
│   └── wsgi.py
├── api/
│   ├── models.py              # All 7 database models
│   ├── serializers.py         # Read + write serializers
│   ├── views.py               # ViewSets with RBAC
│   ├── urls.py                # Router registration
│   ├── permissions.py         # Custom permission classes
│   ├── pagination.py          # 10 results per page
│   ├── admin.py               # Django admin configuration
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py   # Seeds 4 roles + 10 categories
│   └── tests/
│       ├── test_models.py     # 7 model tests
│       └── test_views.py      # 18 API/view tests
├── requirements.txt
├── Procfile                   # Railway: migrate + seed + collectstatic + gunicorn
├── runtime.txt                # python-3.11.9
├── pytest.ini
└── manage.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for development)
- A [Cloudinary](https://cloudinary.com) account (free tier)

### 1. Clone the repository

```bash
git clone https://github.com/Hormoakin/campusserve-backend.git
cd campusserve-backend
```

### 2. Create and activate a virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values (see [Environment Variables](#environment-variables) below).

### 5. Run migrations and seed data

```bash
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

- API: `http://127.0.0.1:8000/api/`
- Swagger UI: `http://127.0.0.1:8000/api/schema/swagger-ui/`

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-very-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Cloudinary (get from cloudinary.com dashboard)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Production Environment Variables (Railway)

| Variable | Description |
|---|---|
| `DJANGO_ENV` | Set to `production` |
| `SECRET_KEY` | Strong random string (50+ chars) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `*` or your Railway domain |
| `CORS_ALLOWED_ORIGINS` | Your Vercel frontend URL |
| `PGDATABASE` | Auto-injected by Railway PostgreSQL |
| `PGHOST` | Auto-injected by Railway PostgreSQL |
| `PGPASSWORD` | Auto-injected by Railway PostgreSQL |
| `PGPORT` | Auto-injected by Railway PostgreSQL |
| `PGUSER` | Auto-injected by Railway PostgreSQL |
| `CLOUDINARY_CLOUD_NAME` | From Cloudinary dashboard |
| `CLOUDINARY_API_KEY` | From Cloudinary dashboard |
| `CLOUDINARY_API_SECRET` | From Cloudinary dashboard |

---

## Running Tests

```bash
# Make sure venv is active and you are in the project root
pytest -v
```

### Test Results

```
collected 25 items

api/tests/test_models.py::TestUserModel::test_create_user                         PASSED
api/tests/test_models.py::TestUserModel::test_default_is_active                   PASSED
api/tests/test_models.py::TestUserModel::test_email_required                      PASSED
api/tests/test_models.py::TestUserModel::test_full_name_property                  PASSED
api/tests/test_models.py::TestServiceRequestModel::test_default_status_is_pending PASSED
api/tests/test_models.py::TestServiceRequestModel::test_reference_number_auto_gen PASSED
api/tests/test_models.py::TestServiceRequestModel::test_reference_numbers_unique  PASSED
api/tests/test_views.py::AuthTests::test_login_success                            PASSED
api/tests/test_views.py::AuthTests::test_login_wrong_password                     PASSED
api/tests/test_views.py::AuthTests::test_register_duplicate_email                 PASSED
api/tests/test_views.py::AuthTests::test_register_password_mismatch               PASSED
api/tests/test_views.py::AuthTests::test_register_success                         PASSED
api/tests/test_views.py::AuthTests::test_unauthenticated_request_rejected         PASSED
api/tests/test_views.py::ServiceRequestTests::test_admin_assigns_request          PASSED
api/tests/test_views.py::ServiceRequestTests::test_admin_sees_all_requests        PASSED
api/tests/test_views.py::ServiceRequestTests::test_create_request_as_student      PASSED
api/tests/test_views.py::ServiceRequestTests::test_export_csv_requires_admin      PASSED
api/tests/test_views.py::ServiceRequestTests::test_export_csv_works_for_admin     PASSED
api/tests/test_views.py::ServiceRequestTests::test_filter_by_status               PASSED
api/tests/test_views.py::ServiceRequestTests::test_invalid_status_transition      PASSED
api/tests/test_views.py::ServiceRequestTests::test_officer_updates_to_in_progress PASSED
api/tests/test_views.py::ServiceRequestTests::test_search_requests                PASSED
api/tests/test_views.py::ServiceRequestTests::test_stats_endpoint                 PASSED
api/tests/test_views.py::ServiceRequestTests::test_status_log_created_on_submit   PASSED
api/tests/test_views.py::ServiceRequestTests::test_student_cannot_see_others      PASSED

========================= 25 passed in 3.82s =========================
```

---

## Deployment

CampusServe backend is deployed on **Railway** with an auto-provisioned **PostgreSQL 18** database.

### Deploy to Railway

1. Push this repository to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub Repo**
3. Select `campusserve-backend`
4. In the same project click **New** → **Database** → **PostgreSQL**
5. Set all environment variables in the **Variables** tab
6. Go to **Settings** → **Deploy** → set **Custom Start Command**:

```
python manage.py migrate && python manage.py seed_data && python manage.py collectstatic --noinput && gunicorn campusserve.wsgi:application --bind 0.0.0.0:$PORT
```

7. Go to **Settings** → **Networking** → **Generate Domain** → enter port `8000`

---

## Academic Context

| Field | Detail |
|---|---|
| **Course** | MIT 8333 — Advanced Web Application Development (Virtual Lab) |
| **Programme** | Master of Information Technology (Software Engineering) |
| **Institution** | Miva Open University |
| **Student** | Ahmed Salman |
| **Student ID** | 2025/A/MIT/0365 |
| **Supervisor** | Dr. Augustine |
| **Academic Session** | 2026/2027 |

---

## Related Repository

- **Frontend:** [github.com/Hormoakin/campusserve-frontend](https://github.com/Hormoakin/campusserve-frontend)

---

<p align="center">Built with ❤️ by Ahmed Salman — CampusServe 2026</p>
