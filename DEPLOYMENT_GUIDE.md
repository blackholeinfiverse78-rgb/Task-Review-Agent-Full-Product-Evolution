# Parikshak Production Deployment Guide

This guide describes how to deploy the Parikshak application to production servers in a hardened configuration.

---

## 1. Environment Configurations
Configure the following inside your production `.env` file:

```env
# Database connection (SQLite is used if fallback is needed, but PostgreSQL is recommended for production concurrency)
DATABASE_URL=postgresql://parikshak_user:secure_pwd@db-host:5432/parikshak_db

# Cryptographic token signing secret key (must be at least 32 characters and distinct from default keys)
JWT_SECRET_KEY=9a8d29841ab7e37e90fdc3f29b9fcd682ae12b5e6fc82fbd72a819d9b8fc272e

# Server settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ALLOWED_ORIGINS=["https://parikshak-frontend.bhiv-governance.org"]
```

---

## 2. Server Installation Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database Schemas
Apply database schema definitions and Alembic migrations:
```bash
alembic upgrade head
```

### Step 3: Run the Startup Security Validation
Verify that environment variables are valid and secrets are non-default:
```bash
python -c "from security.middleware import validate_startup_secrets; validate_startup_secrets()"
```

### Step 4: Run the Production Web Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 3. Docker Deployment (Alternative)
To package and run the application in isolated Docker containers:

### Build Container Image
```bash
docker build -t bhiv/parikshak-backend:latest .
```

### Run Container Instance
```bash
docker run -d \
  --name parikshak-backend \
  -p 8000:8000 \
  --env-file .env \
  bhiv/parikshak-backend:latest
```
