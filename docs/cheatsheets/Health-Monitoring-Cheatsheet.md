# Health Monitoring Cheat Sheet

**Phase:** 07 – Infrastructure Monitoring & Production Readiness

---

# Overview

This cheat sheet provides quick-reference commands and procedures for verifying the health of the DockForge infrastructure.

It is intended to help developers quickly determine whether the application and its dependencies are functioning correctly.

---

# Health Endpoint

## Endpoint

```http
GET /health/
```

Default local URL:

```text
http://localhost/health/
```

---

# Expected Response

A healthy system returns:

```json
{
    "status": "healthy",
    "services": {
        "django": "healthy",
        "database": "healthy",
        "redis": "healthy"
    }
}
```

Status Code:

```text
200 OK
```

---

# Verify Using Browser

Open:

```text
http://localhost/health/
```

If the endpoint returns the expected JSON response, the backend and monitored services are operational.

---

# Verify Using curl

```bash
curl http://localhost/health/
```

---

# Verify Using PowerShell

```powershell
Invoke-WebRequest http://localhost/health/
```

Or:

```powershell
Invoke-RestMethod http://localhost/health/
```

---

# Verify Docker Health

List running services:

```bash
docker compose ps
```

Healthy containers display:

```text
Up (healthy)
```

Example:

```text
NAME         STATUS
django       Up (healthy)
postgres     Up (healthy)
redis        Up (healthy)
nginx        Up
```

---

# Inspect Container Health

```bash
docker inspect <container-name>
```

Useful section:

```json
State:
    Health:
        Status: healthy
```

---

# View Health Logs

Show backend logs:

```bash
docker compose logs django
```

Follow logs in real time:

```bash
docker compose logs -f django
```

---

# Verify PostgreSQL

Access the PostgreSQL container:

```bash
docker compose exec postgres psql
```

Verify connectivity by running a simple query:

```sql
SELECT version();
```

A successful response confirms the database is accepting connections.

---

# Verify Redis

Open the Redis CLI:

```bash
docker compose exec redis redis-cli
```

Test connectivity:

```text
PING
```

Expected response:

```text
PONG
```

---

# Verify Django

Access the Django container:

```bash
docker compose exec django bash
```

Run a basic Django system check:

```bash
python manage.py check
```

Expected output:

```text
System check identified no issues.
```

---

# Common Issues

## Database Unavailable

Symptoms:

- Database connection errors
- Health endpoint reports database failure

Checks:

- PostgreSQL container is running
- Database credentials are correct
- Database service is healthy

---

## Redis Unavailable

Symptoms:

- Cache connection errors
- Redis reported as unavailable

Checks:

- Redis container is running
- Redis service is healthy
- Network connectivity between containers

---

## Django Not Healthy

Symptoms:

- `/health/` unavailable
- Docker reports container as unhealthy

Checks:

- Django logs
- Environment variables
- Database connectivity
- Redis connectivity
- Application startup errors

---

# Startup Verification Checklist

Before beginning development, verify:

- Django container is running
- PostgreSQL container is healthy
- Redis container is healthy
- Nginx container is running
- `/health/` returns `200 OK`
- Docker reports healthy services

---

# Troubleshooting Workflow

```text
Application Issue
        │
        ▼
Check /health/
        │
        ▼
Check docker compose ps
        │
        ▼
Inspect Logs
        │
        ▼
Verify Database
        │
        ▼
Verify Redis
        │
        ▼
Restart Services (if required)
```

---

# Useful Commands

Restart services:

```bash
docker compose restart
```

Restart only Django:

```bash
docker compose restart django
```

Rebuild backend:

```bash
docker compose up --build
```

View running containers:

```bash
docker ps
```

Stop everything:

```bash
docker compose down
```

---

# Best Practices

- Check the `/health/` endpoint after starting the environment.
- Review logs before restarting containers.
- Confirm PostgreSQL and Redis connectivity before debugging application code.
- Keep development and production health checks consistent.
- Use the health endpoint as the primary indicator of backend readiness.

---

# Summary

This cheat sheet provides a quick operational guide for monitoring the health of the DockForge infrastructure.

By combining the health endpoint, Docker health checks, container logs, and service verification commands, developers can rapidly diagnose issues and confirm that the application is ready to serve requests.