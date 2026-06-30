# Parikshak Production Rollback Guide

This playbook outlines procedures to rollback software updates, data events, or schema migrations in production.

---

## 1. Database Schema Rollback
If a database migration causes errors or table corruptions, rollback the database to a prior version using Alembic:

### Rollback Last Applied Migration
```bash
alembic downgrade -1
```

### Rollback to a Specific Migration Revision
```bash
alembic downgrade <revision_id>
```

---

## 2. Event Log & Read Model Rollback (Gov-OS)
If a faulty or unconstitutional human override has been committed to the event ledger:

1. Identify the last known clean sequence ID `N`.
2. Invoke the Gov-OS rollback tool:
   ```bash
   curl -X POST http://localhost:8000/api/v1/gov-os/rollback \
     -H "Authorization: Bearer <GOVERNOR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"target_seq": N}'
   ```
3. This resets the read models and replays events from sequence 1 up to `N`.

---

## 3. Server Deployment Rollback
If a newly deployed container build behaves unstable:

### Rollback Docker Container
Stop the current running container and launch the previously tagged stable build:
```bash
docker stop parikshak-backend
docker rm parikshak-backend
docker run -d --name parikshak-backend -p 8000:8000 --env-file .env bhiv/parikshak-backend:v1.1.0-stable
```

### Rollback Git Code Release
Reset local HEAD commit to previous stable release tag:
```bash
git reset --hard v1.1.0
git pull origin main
```
Restart the uvicorn service.
