# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy only package files first for caching
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Copy rest of frontend files
COPY frontend/ ./

# Build the production bundle
ENV REACT_APP_BACKEND_URL=""
ENV GENERATE_SOURCEMAP=false
ENV CI=false
RUN npm run build

# Stage 2: Python Runner
FROM python:3.11.7-slim
WORKDIR /app

# Install system dependencies (curl needed for healthcheck)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code (backend and other directories)
COPY . .

# Copy build files from frontend builder
COPY --from=frontend-builder /app/frontend/build ./frontend/build/

# Expose port
EXPOSE 8000

# Start FastAPI backend (bind dynamically to cloud provider's injected PORT environment variable)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
