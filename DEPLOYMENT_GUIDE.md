# Parikshak Production Deployment Guide (Render Unified)

This guide describes how to deploy the unified Parikshak application (both FastAPI backend and React frontend SPA) to Render under a single web service.

---

## 1. Environment Configurations
Configure the following environment variables inside your Render web service Dashboard:

```env
# Database connection (SQLite is used if fallback is needed, but PostgreSQL is recommended for production concurrency)
DATABASE_URL=postgresql://parikshak_user:secure_pwd@db-host:5432/parikshak_db

# Cryptographic token signing secret key (must be at least 32 characters and distinct from default keys)
JWT_SECRET_KEY=9a8d29841ab7e37e90fdc3f29b9fcd682ae12b5e6fc82fbd72a819d9b8fc272e

# Allowed CORS origins
ALLOWED_ORIGINS=["https://parikshak.blackholeinfiverse.com"]

# Optional third-party integration keys
GITHUB_TOKEN=your_github_token_here
GROQ_API_KEY=your_groq_key_here
```

---

## 2. Render Web Service Deployment

The repository includes a unified [Dockerfile](file:///g:/Live%20Task%20Review%20Agent%20-%202/Dockerfile) which:
1. Builds the React frontend SPA statically.
2. Embeds the static assets into the Python/FastAPI environment.
3. Serves both frontend and backend on the same port/URL.

### Steps to Deploy:
1. Go to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Connect your repository: `https://github.com/blackholeinfiverse78-rgb/Parikshak-system.git`.
4. Configure the service:
   - **Name**: `parikshak-unified`
   - **Environment / Runtime**: `Docker`
   - **Region**: Select your preferred region (e.g., Oregon)
   - **Branch**: `main`
5. Click **Deploy Web Service**.

---

## 3. Custom Domain Configuration
Once deployed, map your custom domain:
1. Under your Render web service settings, click **Add Custom Domain**.
2. Enter `parikshak.blackholeinfiverse.com`.
3. Configure your DNS provider with a CNAME record:
   - **Name / Host**: `parikshak`
   - **Type**: `CNAME`
   - **Target**: `parikshak-system.onrender.com`

---

## 4. API Verification Links
- **Production URL**: `https://parikshak.blackholeinfiverse.com`
- **Health Check**: `https://parikshak.blackholeinfiverse.com/health`
- **Swagger API Docs**: `https://parikshak.blackholeinfiverse.com/docs`
