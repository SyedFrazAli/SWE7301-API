# SWE7301-API: GeoScope Analytics Platform

## Complete Setup Guide (New System)

### Prerequisites

- Python 3.8+ installed
- Git installed
- Windows PowerShell

### Step 1: Clone and Setup Project

```powershell
# Clone the repository
git clone <your-repo-url>
cd SWE7301-API

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate.ps1
```

### Step 2: Backend Setup (Flask API)

```powershell
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start Flask backend server
python run.py
```

**Backend will run on:** http://127.0.0.1:5000

### Step 3: Frontend Setup (Django Website)

```powershell
# Open new PowerShell terminal
# Activate virtual environment
cd SWE7301-API
venv\Scripts\Activate.ps1

# Navigate to frontend directory
cd frontend

# Install Django dependencies
pip install -r requirements.txt
# Added more packages to requirements.txt

# Run database migrations
python manage.py migrate

# Start Django frontend server
python manage.py runserver 8001
```

**Frontend will run on:** http://127.0.0.1:8001

### Step 4: Test the Application

1. **Open browser to:** http://127.0.0.1:8001
2. **Login with:** `admin` / `password`
3. **Access JWT Dashboard** to test US-16 token management features

---

## Quick Start (Existing Setup)

### Option 1: Using the batch file (from project root)

```bash
run_django.bat
```

### Option 2: Manual commands

```bash
# Activate environment
venv\Scripts\Activate.ps1

# Backend
cd backend
python run.py

# Frontend (new terminal)
cd frontend
python manage.py migrate
python manage.py runserver 8001
```

---

## Project Folder Structure

```
SWE7301-API
├─ backend_otp.txt
├─ migrate_db.py
├─ README.md
├─ setup.ps1
├─ US-16-COMPLETE.md
├─ verify_access.py
├─ backend/
│  ├─ backend_otp.txt
│  ├─ Procfile
│  ├─ requirements.txt
│  ├─ run.py
│  ├─ seed_data.py
│  ├─ seed_test_user.py
│  ├─ verify_test_login.py
│  ├─ wsgi.py
│  └─ app/
│     ├─ __init__.py
│     ├─ db.py
│     ├─ auth/
│     │  └─ swaggerHealthApi.py
│     ├─ models/
│     │  ├─ __init__.py
│     │  └─ jwtAuth.py
│     ├─ routes/
│     │  ├─ bulk12.py
│     │  ├─ filtering.py
│     │  ├─ healthApi.py
│     │  ├─ httpEndpoints07.py
│     │  └─ jsonDataFormat08.py
│     └─ tests/
│        ├─ test_app.py
│        ├─ test_US_06.py
│        ├─ test_US_13.py
├─ frontend/
│  ├─ __init__.py
│  ├─ db.sqlite3
│  ├─ manage.py
│  ├─ Procfile
│  ├─ README.md
│  ├─ requirements.txt
│  ├─ config/
│  │  ├─ __init__.py
│  │  ├─ asgi.py
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ wsgi.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ admin.py
│  │  ├─ apps.py
│  │  ├─ forms.py
│  │  ├─ models.py
│  │  ├─ tests.py
│  │  └─ views.py
│  ├─ static/
│  │  ├─ app.js
│  │  ├─ landing.css
│  │  ├─ login.css
│  │  ├─ signup.css
│  │  ├─ signup.js
│  │  ├─ styles.css
│  │  └─ images/
│  └─ templates/
│     ├─ dashboard.html
│     ├─ index.html
│     ├─ login.html
│     ├─ payment_failed.html
│     ├─ payment_success.html
│     ├─ settings.html
│     ├─ setup_2fa.html
│     ├─ signup.html
│     └─ subscriptions.html
```

---

## Architecture Overview

### Backend (Flask) - Port 5000

- **JWT Authentication** (US-13, US-16)
- **RESTful APIs** for geospatial data
- **Token Management** (access/refresh tokens)
- **Health Monitoring** endpoints

### Frontend (Django) - Port 8001

- **User Interface** for authentication
- **Dashboard** with JWT token management
- **Signup/Login** pages
- **Product Subscriptions** interface

---

## Features Implemented

### US-13: Authentication and Protected Routes ✅

- JWT-based authentication
- Protected API endpoints
- Bearer token validation

### US-14: Django Website - Basic Setup ✅

- Django frontend application
- User authentication forms
- Dashboard interface
- Static asset management

### US-16: JWTs via Website ✅

- **Token Generation**: Valid JWTs issued through website
- **Token Refresh**: Automatic token renewal when expired
- **Dashboard Integration**: Real-time token management
- **Session Management**: Secure token storage

---

## API Endpoints

### Authentication

- `POST /login` - User authentication with JWT tokens
- `POST /signup` - User registration
- `POST /refresh` - Refresh expired access tokens
- `POST /token/validate` - Validate current JWT status

### Protected Routes

- `GET /protected` - Test JWT authentication
- `GET /api/products` - Available subscription products
- `GET /api/subscriptions` - User subscriptions

---

## Environment Variables

Create `.env` file in project root:

```env
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
BACKEND_URL=http://127.0.0.1:5000
DEBUG=True
```

---

## Troubleshooting

### Virtual Environment Issues

```powershell
# If activation fails, try:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then retry activation:
venv\Scripts\Activate.ps1
```

### Port Conflicts

- Backend default: 5000 (configurable in `run.py`)
- Frontend default: 8001 (configurable via `runserver` command)

### Database Issues

```powershell
# Reset Django database
cd frontend
rm db.sqlite3
python manage.py migrate
```

### Dependencies Issues

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```
