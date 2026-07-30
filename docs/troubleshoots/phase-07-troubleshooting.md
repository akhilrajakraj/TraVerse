# Phase 07 Troubleshooting Guide

**Phase:** 07 – Infrastructure Monitoring & Production Readiness

---

# Overview

This guide documents common issues that may occur while working with the DockForge infrastructure introduced during Phase 07.

Each section describes:

- Symptoms
- Possible causes
- Resolution steps
- Prevention tips

The goal is to reduce debugging time and provide a repeatable troubleshooting process.

---

# General Troubleshooting Workflow

When an issue occurs, follow this sequence:

```
Problem Detected
        │
        ▼
Check Container Status
        │
        ▼
Verify Health Endpoint
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
Review Environment Configuration
        │
        ▼
Restart or Rebuild Services
```

---

# Issue 1 – Docker Containers Fail to Start

## Symptoms

- One or more containers exit immediately
- `docker compose up` fails
- Startup process stops unexpectedly

## Possible Causes

- Invalid Docker Compose configuration
- Incorrect environment variables
- Port conflicts
- Missing images
- Docker daemon not running

## Resolution

Check container status:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs
```

Validate the Compose configuration:

```bash
docker compose config
```

If necessary, rebuild the images:

```bash
docker compose up --build
```

## Prevention

- Verify Compose files before committing changes.
- Keep environment files up to date.
- Avoid port conflicts with other applications.

---

# Issue 2 – Django Container Reports "Unhealthy"

## Symptoms

- Docker shows:

```text
Up (unhealthy)
```

- `/health/` is unavailable
- Nginx returns errors when accessing the backend

## Possible Causes

- Django startup failure
- Database unavailable
- Redis unavailable
- Health endpoint returning errors
- Application configuration issues

## Resolution

Check the health endpoint:

```text
http://localhost/health/
```

Inspect logs:

```bash
docker compose logs django
```

Verify PostgreSQL and Redis connectivity before restarting the backend.

## Prevention

- Test configuration changes locally.
- Ensure dependencies are available before startup.
- Keep health checks aligned with the application.

---

# Issue 3 – PostgreSQL Connection Failure

## Symptoms

- Database connection errors
- Migration failures
- Health endpoint reports database issues

## Possible Causes

- PostgreSQL container stopped
- Incorrect database credentials
- Network configuration problems
- Database not fully initialized

## Resolution

Check the PostgreSQL container:

```bash
docker compose ps
```

Open the database shell:

```bash
docker compose exec postgres psql
```

Verify database connectivity:

```sql
SELECT version();
```

Review PostgreSQL logs:

```bash
docker compose logs postgres
```

## Prevention

- Verify environment variables before deployment.
- Allow PostgreSQL to finish initialization before dependent services start.

---

# Issue 4 – Redis Connection Failure

## Symptoms

- Cache errors
- Redis unavailable in health checks
- Application startup warnings

## Possible Causes

- Redis container stopped
- Network communication issues
- Incorrect Redis configuration

## Resolution

Access Redis:

```bash
docker compose exec redis redis-cli
```

Run:

```text
PING
```

Expected response:

```text
PONG
```

Review logs:

```bash
docker compose logs redis
```

## Prevention

- Confirm Redis is running before starting development.
- Keep Redis configuration synchronized across environments.

---

# Issue 5 – Health Endpoint Returns Errors

## Symptoms

- `/health/` does not return `200 OK`
- Docker marks the backend as unhealthy
- Dependent services do not start

## Possible Causes

- One or more dependency checks failing
- Database unavailable
- Redis unavailable
- Application startup incomplete

## Resolution

Check:

```text
GET /health/
```

Then verify:

- Django logs
- PostgreSQL status
- Redis status
- Container health

Resolve the underlying dependency issue before restarting services.

## Prevention

- Verify infrastructure after every startup.
- Keep health checks lightweight and reliable.

---

# Issue 6 – Nginx Cannot Reach Django

## Symptoms

- 502 Bad Gateway
- Requests fail through Nginx
- Direct backend access works

## Possible Causes

- Django container not healthy
- Incorrect upstream configuration
- Startup sequencing issues

## Resolution

Verify:

```bash
docker compose ps
```

Ensure Django reports:

```text
Up (healthy)
```

Review Nginx logs:

```bash
docker compose logs nginx
```

Confirm the backend is accessible internally before troubleshooting Nginx configuration.

## Prevention

- Use health-based startup dependencies.
- Verify reverse proxy configuration after infrastructure changes.

---

# Issue 7 – Logging Does Not Appear

## Symptoms

- Missing application logs
- Log files remain empty
- Console output unavailable

## Possible Causes

- Logging configuration errors
- Incorrect file permissions
- Logger not initialized
- Wrong logging level

## Resolution

Verify the logging configuration.

Restart the backend:

```bash
docker compose restart django
```

Inspect console output:

```bash
docker compose logs django
```

## Prevention

- Validate logging after configuration changes.
- Use consistent logging levels across environments.

---

# Issue 8 – Changes Are Not Reflected

## Symptoms

- Source code changes do not appear
- Old application behavior continues

## Possible Causes

- Cached Docker image
- Volume configuration issues
- Rebuild not performed

## Resolution

Rebuild containers:

```bash
docker compose up --build
```

If necessary:

```bash
docker compose build --no-cache
```

Restart the environment.

## Prevention

- Rebuild after dependency changes.
- Confirm volume mappings in the development Compose configuration.

---

# Diagnostic Checklist

When debugging, verify:

- Docker daemon is running
- Containers are running
- Django container is healthy
- PostgreSQL is available
- Redis is available
- `/health/` returns `200 OK`
- Logs contain no startup errors
- Environment variables are correctly configured

---

# Best Practices

- Investigate logs before restarting containers.
- Resolve dependency failures before debugging application code.
- Test health checks after infrastructure changes.
- Keep development and production configurations synchronized where appropriate.
- Document recurring issues for future reference.

---

# Summary

Phase 07 introduced infrastructure features that improve reliability but also add operational complexity.

This troubleshooting guide provides a structured process for diagnosing Docker, Django, PostgreSQL, Redis, health monitoring, and logging issues, enabling faster recovery and more consistent development workflows.