# MediCore HMS

**A full-stack Hospital Management Information System** built with Django REST Framework (backend) and React (frontend). Designed for Kenyan healthcare facilities with support for NHIF/SHA, eTIMS, M-Pesa, and multi-role clinical workflows.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [User Roles & Access](#user-roles--access)
- [API Overview](#api-overview)
- [Frontend Pages](#frontend-pages)
- [Environment Variables](#environment-variables)
- [Database Models](#database-models)
- [Development Notes](#development-notes)

---

## Features

| Module | Features |
|---|---|
| **Reception** | Patient registration, OPD visit check-in, appointment booking, queue management |
| **Triage** | Colour-coded triage (RED/ORANGE/YELLOW/GREEN/BLUE), vital signs, pain scoring |
| **Consultation** | Doctor workspace, diagnosis, prescriptions, lab & imaging orders, follow-up |
| **Pharmacy** | Prescription dispensing, OTC sales, stock management, inpatient medicine requests |
| **Laboratory** | Order processing, sample tracking, result entry, critical result flagging |
| **Radiology** | Imaging study workflow, radiology report submission |
| **Inpatient** | Ward/bed management, admissions, daily charges, vitals, discharge |
| **Emergency** | Emergency bed management, casualty visits, emergency prescriptions |
| **Cashier** | Payment processing (Cash/M-Pesa/Insurance/NHIF), session management, daily reports |
| **Insurance** | Claims for consultation, pharmacy, and inpatient; SHA integration |
| **Procurement** | Suppliers, purchase requests, purchase orders, goods received notes |
| **Admin** | User management, hospital settings, system configuration, integrations |
| **Attendance** | Staff check-in/out, leave applications |

---

## Tech Stack

### Backend
- **Python 3.11+** / **Django 4.2**
- **Django REST Framework** — RESTful API
- **SimpleJWT** — JWT authentication (8hr access / 1day refresh)
- **Django Channels** — WebSocket support (notifications)
- **django-cors-headers** — CORS for frontend dev server
- **django-filter** — Advanced query filtering
- **SQLite** (dev) / **PostgreSQL** (production)

### Frontend
- **React 18** with Vite
- **React Router v6** — client-side routing
- **Axios** — HTTP client with JWT interceptor + auto-refresh
- **Bootstrap 5.3** — layout and base components
- **Bootstrap Icons** — icon library
- **DM Sans** (Google Fonts) — primary typeface
- Custom CSS design system (`src/styles/main.css`)

---

## Project Structure

```
medicore/
├── backend/                          # Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── medicore/                     # Django project config
│   │   ├── __init__.py
│   │   ├── settings.py               # All settings incl. JWT, CORS, Channels
│   │   ├── urls.py                   # Root URL dispatcher
│   │   ├── wsgi.py
│   │   └── asgi.py                   # Channels ASGI entry point
│   └── api/                          # Single Django app — all hospital models
│       ├── __init__.py
│       ├── apps.py
│       ├── admin.py                  # Django admin registrations
│       ├── models.py                 # All 50+ database models  ← place user-provided file here
│       ├── serializers.py            # DRF serializers for all models
│       ├── views.py                  # 40+ ViewSets with role-based permissions
│       └── urls.py                   # DRF DefaultRouter — all endpoints
│
└── frontend/                         # React + Vite SPA
    ├── package.json
    ├── vite.config.js                # Vite config with /api proxy
    ├── index.html                    # Bootstrap 5, Bootstrap Icons, Google Fonts
    ├── .env.example
    └── src/
        ├── main.jsx                  # React 18 entry point
        ├── App.jsx                   # Auth context, role routing, all routes
        ├── services/
        │   └── api.js                # Axios instance + all API modules
        ├── styles/
        │   └── main.css              # CSS design system (variables, components)
        ├── components/
        │   ├── common/
        │   │   └── index.jsx         # Shared UI: StatCard, Modal, DataTable, etc.
        │   └── layout/
        │       └── Layout.jsx        # App shell: sidebar + topbar
        └── pages/
            ├── Login.jsx
            ├── admin/
            │   ├── Dashboard.jsx     # System stats, staff overview
            │   ├── Users.jsx         # User management (create, edit, roles)
            │   └── Settings.jsx      # Hospital info, system config, integrations
            ├── receptionist/
            │   ├── Dashboard.jsx     # Live visit stats, active visits
            │   ├── Patients.jsx      # Patient search, register, edit
            │   ├── Visits.jsx        # Register OPD visits, insurance, queue
            │   ├── Queue.jsx         # Real-time multi-department queue
            │   └── Appointments.jsx  # Book and manage appointments
            ├── nurse/
            │   ├── Dashboard.jsx     # Triage queue, priority summary
            │   ├── Triage.jsx        # Full triage assessment form
            │   ├── Vitals.jsx        # Record inpatient vital signs
            │   └── Inpatient.jsx     # Ward rounds, medicine requests
            ├── doctor/
            │   ├── Dashboard.jsx     # Greeting, waiting queue, today's schedule
            │   ├── Consultation.jsx  # Clinical workspace: diagnosis, Rx, labs, imaging
            │   ├── Patients.jsx      # Patient records and medical history
            │   ├── LabOrders.jsx     # Track lab orders and results
            │   └── Imaging.jsx       # Track imaging study requests
            ├── pharmacy/
            │   ├── Dashboard.jsx     # Pending Rx, low stock alerts, inpatient requests
            │   ├── Dispense.jsx      # Dispense OPD prescriptions
            │   ├── Stock.jsx         # Formulary CRUD, stock adjustments
            │   ├── OTC.jsx           # Cart-based over-the-counter sales
            │   └── InpatientRequests.jsx  # Approve/dispense ward requests
            ├── cashier/
            │   ├── Dashboard.jsx     # Session management, revenue summary
            │   ├── Payments.jsx      # Process Cash/M-Pesa/Insurance payments
            │   └── Reports.jsx       # Date-range revenue reports
            ├── lab/
            │   ├── Dashboard.jsx     # Order pipeline stats
            │   ├── Orders.jsx        # Sample collection → processing flow
            │   └── Results.jsx       # Enter findings, mark critical
            └── radiology/
                ├── Dashboard.jsx     # Modality breakdown, active studies
                └── Studies.jsx       # Study workflow + radiology report submission
```

---

## Quick Start

### 1. Clone and set up the backend

```bash
cd medicore/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment file
cp .env.example .env

# Place your models.py in api/models.py  (the file provided separately)

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser (admin)
python manage.py createsuperuser

# Seed triage categories (run in Django shell)
python manage.py shell
```

```python
from api.models import TriageCategory
TriageCategory.objects.bulk_create([
    TriageCategory(name="Immediate",   color_code="RED",    max_wait_time=0,   priority_order=1),
    TriageCategory(name="Very Urgent", color_code="ORANGE", max_wait_time=10,  priority_order=2),
    TriageCategory(name="Urgent",      color_code="YELLOW", max_wait_time=30,  priority_order=3),
    TriageCategory(name="Standard",    color_code="GREEN",  max_wait_time=60,  priority_order=4),
    TriageCategory(name="Non-Urgent",  color_code="BLUE",   max_wait_time=120, priority_order=5),
])
```

```bash
# Start the development server
python manage.py runserver
# API available at http://localhost:8000/api/
# Admin panel at  http://localhost:8000/admin/
```

### 2. Set up the frontend

```bash
cd medicore/frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start dev server
npm run dev
# App available at http://localhost:5173
```

### 3. Create users for each role

Log in to the Django admin at `http://localhost:8000/admin/` and create users with these `user_type` values:

| Role | user_type value |
|---|---|
| Administrator | `ADMIN` |
| Receptionist | `RECEPTIONIST` |
| Nurse | `NURSE` |
| Doctor | `DOCTOR` |
| Pharmacist | `PHARMACIST` |
| Cashier | `CASHIER` |
| Lab Technician | `LAB_TECH` |
| Radiologist | `RADIOLOGIST` |
| Insurance Officer | `INSURANCE` |

Alternatively, use the **Admin → Users** page in the frontend after logging in as a superuser.

---

## User Roles & Access

Each role gets a dedicated dashboard and navigation after login. The system redirects automatically based on `user_type`.

```
ADMIN        →  /admin/dashboard
RECEPTIONIST →  /reception/dashboard
NURSE        →  /nurse/dashboard
DOCTOR       →  /doctor/dashboard
PHARMACIST   →  /pharmacy/dashboard
CASHIER      →  /cashier/dashboard
LAB_TECH     →  /lab/dashboard
RADIOLOGIST  →  /radiology/dashboard
```

---

## API Overview

Base URL: `http://localhost:8000/api/`

Authentication: `Authorization: Bearer <access_token>`

| Endpoint group | Path prefix |
|---|---|
| Auth | `/api/auth/` |
| Patients | `/api/patients/` |
| Appointments | `/api/appointments/` |
| Consultations | `/api/consultations/` |
| Prescriptions | `/api/prescriptions/` |
| Medicines | `/api/medicines/` |
| OTC Sales | `/api/otc-sales/` |
| Patient Visits | `/api/visits/` |
| Triage | `/api/triage/` |
| Queue | `/api/queue/` |
| Lab Tests | `/api/lab-tests/` |
| Lab Orders | `/api/lab-orders/` |
| Lab Results | `/api/lab-results/` |
| Imaging | `/api/imaging/` |
| Wards | `/api/wards/` |
| Beds | `/api/beds/` |
| Inpatient Admissions | `/api/admissions/` |
| Emergency Visits | `/api/emergency-visits/` |
| Suppliers | `/api/suppliers/` |
| Purchase Requests | `/api/purchase-requests/` |
| Purchase Orders | `/api/purchase-orders/` |
| Goods Received | `/api/grn/` |
| Insurance Claims | `/api/claims/consultation/` etc. |
| SHA | `/api/sha/members/`, `/api/sha/claims/` |
| Notifications | `/api/notifications/` |
| Cashier Sessions | `/api/cashier-sessions/` |
| Payment Audit Log | `/api/payment-logs/` |
| Attendance | `/api/attendance/` |
| Leave | `/api/leave/` |
| Dashboard | `/api/dashboard/` |

### Key custom actions

```
POST /api/auth/login/                     — obtain JWT tokens
POST /api/auth/logout/                    — blacklist refresh token
GET  /api/auth/me/                        — current user profile

POST /api/visits/{id}/update_status/      — update visit status
GET  /api/visits/waiting/                 — patients waiting

POST /api/triage/                         — create triage assessment

POST /api/queue/{id}/call_patient/        — call patient to service point
POST /api/queue/{id}/complete/            — mark service complete

POST /api/consultations/{id}/add_prescription/  — add Rx to consultation

POST /api/prescriptions/{id}/dispense/    — dispense a prescription

GET  /api/medicines/low_stock/            — medicines below reorder level
POST /api/medicines/{id}/adjust_stock/    — stock adjustment

POST /api/admissions/{id}/discharge/      — discharge inpatient
POST /api/admissions/{id}/add_charge/     — add daily charge

POST /api/medicine-requests/{id}/approve/ — pharmacy approve inpatient Rx
POST /api/medicine-requests/{id}/dispense/— pharmacy dispense inpatient Rx

GET  /api/dashboard/stats/                — summary statistics
GET  /api/dashboard/revenue_chart/        — revenue over time
GET  /api/dashboard/recent_activity/      — activity feed
```

---

## Frontend Pages

### Common components (`src/components/common/index.jsx`)

| Component | Purpose |
|---|---|
| `StatCard` | Dashboard metric cards with icon and colour variants |
| `LoadingSpinner` | Centered loading indicator |
| `EmptyState` | Empty list placeholder with icon and message |
| `Badge` | Coloured label badge |
| `Modal` | Overlay modal with header/body/footer |
| `ConfirmModal` | Confirmation dialog |
| `DataTable` | Sortable table from column config + data array |
| `SearchInput` | Debounced search input |
| `PageHeader` | Page title + subtitle + action button slot |
| `Tabs` | Horizontal tab switcher |
| `ToastContainer` / `useToast` | Toast notification system |
| `FormRow` | Label + input wrapper with Bootstrap grid class |
| `SectionCard` | Titled card section |
| `VitalBox` | Vital sign display chip |
| `TriageBadge` | Colour-coded triage category badge |
| `StatusBadge` | Generic status badge |

### CSS Design Tokens (`src/styles/main.css`)

```css
--mc-blue:    #1a6fdd   /* primary brand */
--mc-teal:    #0d9488
--mc-sidebar: #0f172a   /* dark sidebar bg */
--sidebar-width: 260px
--topbar-height: 64px
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key (required) |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `localhost` | Comma-separated allowed hosts |
| `DATABASE_URL` | SQLite | Postgres: `postgres://user:pass@host/db` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Frontend origins |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Django API base URL |

---

## Database Models

All models live in `api/models.py`. Key model groups:

**Users & Staff**
`User` (custom), `Doctor`, `Nurse`

**Patients**
`Patient`, `MedicalHistory`, `PatientVisit`

**Clinical**
`Appointment`, `Consultation`, `Prescription`, `ICD10Code`

**Triage & Queue**
`TriageCategory`, `TriageAssessment`, `QueueManagement`

**Pharmacy**
`Medicine`, `StockMovement`, `OTCSale`, `OTCSaleItem`

**Laboratory**
`LabTest`, `LabOrder`, `LabOrderItem`, `LabResult`

**Radiology**
`ImagingStudy`

**Inpatient**
`Ward`, `Bed`, `InpatientAdmission`, `InpatientDailyCharge`, `InpatientVitals`, `InpatientMedicineRequest`

**Emergency**
`EmergencyBed`, `EmergencyVisit`, `EmergencyCharge`, `EmergencyMedicineRequest`

**Procurement**
`Supplier`, `PurchaseRequest`, `PurchaseRequestItem`, `PurchaseOrder`, `PurchaseOrderItem`, `GoodsReceivedNote`, `GoodsReceivedNoteItem`

**Insurance & SHA**
`InsuranceProvider`, `SpecializedService`, `ConsultationInsuranceClaim`, `PharmacyInsuranceClaim`, `InpatientInsuranceClaim`, `SHAMember`, `SHAClaim`

**Finance**
`PaymentAuditLog`, `CashierSession`

**HR**
`Attendance`, `LeaveApplication`

**System**
`Notification`

---

## Development Notes

### Adding a new role

1. Add the `user_type` constant to `User.USER_TYPES` in `models.py`
2. Add a permission class in `views.py` (e.g. `IsNewRole`)
3. Add NAV config in `Layout.jsx` under `NAV_CONFIG`
4. Add routes in `App.jsx` under the new role prefix
5. Create page components under `src/pages/<rolename>/`

### JWT Token Flow

```
Login → POST /api/auth/login/ → { access, refresh }
       ↓ store in localStorage
Every request → Authorization: Bearer <access>
       ↓ 401 response
Axios interceptor → POST /api/auth/token/refresh/ → new access
       ↓ retry original request
Logout → POST /api/auth/logout/ (blacklists refresh)
```

### Running in production

```bash
# Backend — collect static files and use gunicorn
python manage.py collectstatic
gunicorn medicore.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend — build static files
npm run build
# Serve dist/ via nginx or any static host
```

---

## License

Private / internal use. All rights reserved.