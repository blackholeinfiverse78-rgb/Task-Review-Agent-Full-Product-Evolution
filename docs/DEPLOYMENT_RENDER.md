# 🚀 Deploying to Render: Unified Web Service

This guide explains how to deploy the **Parikshak** system as a single unified web service on Render, serving both the FastAPI backend and the React frontend from a single URL.

---

## 1. Unified Architecture Overview

Instead of deploying separate backend services and static frontends, the project compiles everything into a single Docker image:
- **Build Stage**: React frontend is built statically with API base URL configured to root (`/`).
- **Serve Stage**: FastAPI mounts the React build directory, serving SPA files under `/{catchall}` and API endpoints under `/api/v1`.

This provides:
- ✅ **A single deployed link** (`https://parikshak.blackholeinfiverse.com`).
- ✅ **Zero CORS configuration complexity** between frontend and backend.
- ✅ **Simplified deployment** on Render.

---

## 2. Deploying via render.yaml (Blueprint)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect [render.yaml](file:///g:/Live%20Task%20Review%20Agent%20-%202/render.yaml).
5. Click **Apply**.

---

## 3. Manual Web Service Deploy (Alternative)

1. Click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the following:
   - **Name**: `parikshak-unified`
   - **Language**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
4. Add the following **Environment Variables**:
   - `DATABASE_URL`: `postgresql://parikshak_user:secure_pwd@db-host:5432/parikshak_db`
   - `JWT_SECRET_KEY`: `[your-custom-secure-key]`
   - `ALLOWED_ORIGINS`: `["https://parikshak.blackholeinfiverse.com"]`
5. Click **Deploy Web Service**.

---

## 4. Subdomain Mapping (`parikshak.blackholeinfiverse.com`)

1. In the Web Service settings on Render, go to the **Custom Domains** section.
2. Click **Add Custom Domain** and enter:
   `parikshak.blackholeinfiverse.com`
3. Point your DNS provider's CNAME record for `parikshak` to:
   `parikshak-system.onrender.com`

---

## 5. Expected Production URLs
- **Main App Portal**: `https://parikshak.blackholeinfiverse.com`
- **API Swagger Documentation**: `https://parikshak.blackholeinfiverse.com/docs`
- **System Health Checks**: `https://parikshak.blackholeinfiverse.com/health`
