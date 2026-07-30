# Phase 06 Troubleshooting Guide

**Project:** DockForge

**Phase:** 06 — Enterprise Docker Compose & Infrastructure Orchestration

---

# Introduction

Building infrastructure is only one part of backend engineering.

The other equally important skill is diagnosing problems when things do not work as expected.

This guide documents every significant issue encountered during Phase 6 while building DockForge's Docker Compose infrastructure.

Rather than simply presenting solutions, each section explains:

- Symptoms
- Root Cause
- Investigation Process
- Resolution
- Lessons Learned

The objective is to teach students how experienced backend engineers approach debugging.

---

# Debugging Methodology

Before examining individual problems, it is important to understand the debugging workflow used throughout this phase.

Whenever an issue occurred, the following process was followed.

```
Observe Problem

↓

Collect Evidence

↓

Verify Infrastructure

↓

Identify Root Cause

↓

Apply Fix

↓

Rebuild

↓

Validate Solution
```

Rather than guessing, every problem was investigated systematically.

---

# Issue 1 — Django Failed During Startup

## Symptoms

The Django container exited during startup.

Container logs displayed:

```
ModuleNotFoundError

No module named 'django_redis'
```

---

## Investigation

The following commands were executed:

```bash
docker compose ps
```

Result:

- PostgreSQL Healthy
- Redis Healthy
- Django Failed

This immediately suggested that infrastructure was functioning correctly.

The failure originated inside the Django application.

---

## Root Cause

The Redis cache backend had been configured inside Django.

However, the required Python package was missing.

Missing dependency:

```
django-redis
```

---

## Resolution

Added:

```
django-redis==7.0.0
```

to:

```
backend/requirements/base.txt
```

Rebuilt the image.

```bash
docker compose up --build -d
```

---

## Validation

Executed:

```bash
docker compose logs django
```

Observed:

```
System check identified no issues.

Starting development server...
```

Problem resolved.

---

## Lesson Learned

Not every Docker problem is a Docker problem.

Infrastructure and application dependencies should always be investigated separately.

---

# Issue 2 — localhost No Longer Worked

## Symptoms

Initially, Django connected to PostgreSQL using:

```
POSTGRES_HOST=localhost
```

After moving Django into Docker Compose, this configuration became invalid.

---

## Root Cause

Inside a Docker container:

```
localhost
```

always refers to that container itself.

The PostgreSQL database executes inside a different container.

---

## Resolution

Updated environment configuration.

Old:

```
POSTGRES_HOST=localhost

REDIS_HOST=localhost
```

New:

```
POSTGRES_HOST=postgres

REDIS_HOST=redis
```

Docker automatically resolves service names through its internal DNS.

---

## Lesson Learned

Containers communicate using service names, not localhost.

---

# Issue 3 — Build Context Selection

## Symptoms

Before integrating Django into Compose, the correct build context was uncertain.

The Dockerfile resided inside:

```
infrastructure/docker/django/
```

while project files resided in:

```
backend/
```

---

## Investigation

The project structure was reviewed carefully.

The objective was to ensure COPY instructions continued to function correctly.

---

## Resolution

Configured:

```yaml
build:
  context: ../../
```

This allowed Docker to access the project root.

---

## Lesson Learned

The build context determines which files Docker can access during image creation.

Choosing the wrong context often results in COPY failures.

---

# Issue 4 — Startup Dependencies

## Symptoms

Django depends on PostgreSQL and Redis.

Without dependency management, startup order becomes unpredictable.

---

## Resolution

Implemented:

```yaml
depends_on:
  postgres:
    condition: service_healthy

  redis:
    condition: service_healthy
```

---

## Validation

Observed startup order:

```
PostgreSQL

↓

Healthy

↓

Redis

↓

Healthy

↓

Django
```

---

## Lesson Learned

Container creation order is not the same as service readiness.

Health checks should be combined with depends_on.

---

# Issue 5 — Restart Policy Verification

## Objective

Verify how:

```yaml
restart: unless-stopped
```

actually behaves.

---

## Experiment

Executed:

```bash
docker stop dockforge-redis
```

---

## Observation

Redis remained stopped.

Docker did not restart the container.

---

## Explanation

Manual shutdown is intentional.

The restart policy only handles unexpected failures.

---

## Lesson Learned

Always verify infrastructure behavior experimentally.

Documentation should support observation rather than assumptions.

---

# Issue 6 — Service Name Typo

## Symptoms

Executed:

```bash
docker compose logs django\
```

Docker returned:

```
no such service: django\
```

---

## Root Cause

The backslash became part of the service name.

Docker attempted to locate a service literally named:

```
django\
```

---

## Resolution

Executed:

```bash
docker compose logs django
```

Problem resolved immediately.

---

## Lesson Learned

Small command-line mistakes can produce misleading errors.

Always verify the exact command entered.

---

# Issue 7 — Missing Python Dependencies

## Symptoms

The Docker image built successfully.

The container started.

The application failed.

---

## Explanation

Docker only installs packages listed inside:

```
requirements/base.txt
```

Packages installed locally inside the virtual environment are not automatically included in Docker images.

---

## Resolution

Every required dependency must be explicitly listed inside the requirements file before rebuilding the image.

---

## Lesson Learned

The Docker image represents an isolated Python environment.

Never assume your local virtual environment matches the container.

---

# Infrastructure Validation Checklist

Whenever DockForge infrastructure behaves unexpectedly, verify the following.

---

## Check Container Status

```bash
docker compose ps
```

---

## View Django Logs

```bash
docker compose logs django
```

---

## View PostgreSQL Logs

```bash
docker compose logs postgres
```

---

## View Redis Logs

```bash
docker compose logs redis
```

---

## Validate Compose Configuration

```bash
docker compose config
```

---

## Rebuild Everything

```bash
docker compose down

docker compose up --build -d
```

---

## Inspect Networks

```bash
docker network ls

docker network inspect
```

---

## Inspect Volumes

```bash
docker volume ls

docker volume inspect
```

---

# General Debugging Strategy

When troubleshooting Docker infrastructure, avoid making assumptions.

Instead follow this sequence.

```
Container Running?

↓

Healthy?

↓

Logs

↓

Environment Variables

↓

Network

↓

Dependencies

↓

Application Code
```

This approach isolates infrastructure issues from application issues.

---

# Common Beginner Mistakes

- Using localhost inside containers
- Forgetting to rebuild after changing requirements
- Ignoring container logs
- Assuming Running means Ready
- Hardcoding configuration
- Forgetting health checks
- Misunderstanding build context
- Confusing Docker image with Docker container

---

# Final Advice

Successful backend engineers are not those who never encounter errors.

They are the ones who investigate problems methodically, verify assumptions with evidence, and understand the interaction between infrastructure and application code.

Every issue documented in this guide was encountered during the development of DockForge and contributed to a deeper understanding of Docker Compose and enterprise backend infrastructure.