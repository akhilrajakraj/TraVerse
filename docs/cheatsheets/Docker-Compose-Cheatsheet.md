# Docker Compose Cheat Sheet

**Phase:** 07 – Infrastructure Monitoring & Production Readiness

---

# Overview

This cheat sheet provides quick-reference Docker Compose commands used throughout the DockForge project.

The commands are organized by common development and infrastructure tasks.

---

# Project Structure

Navigate to the Compose directory before executing commands.

```bash
cd infrastructure/compose
```

---

# Development Environment

## Start Development Environment

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.dev.yml \
up
```

---

## Start in Detached Mode

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.dev.yml \
up -d
```

---

## Rebuild Development Containers

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.dev.yml \
up --build
```

---

# Production Environment

## Start Production Environment

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.prod.yml \
up -d
```

> Ensure `production.env` contains valid production configuration before starting the production environment.

---

## Rebuild Production Images

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.prod.yml \
up --build -d
```

---

# Container Management

## List Running Containers

```bash
docker compose ps
```

---

## View All Containers

```bash
docker ps -a
```

---

## Stop Containers

```bash
docker compose stop
```

---

## Start Existing Containers

```bash
docker compose start
```

---

## Restart Containers

```bash
docker compose restart
```

---

## Remove Containers

```bash
docker compose down
```

---

# Build Operations

## Build Images

```bash
docker compose build
```

---

## Force Image Rebuild

```bash
docker compose build --no-cache
```

---

## Pull Latest Base Images

```bash
docker compose pull
```

---

# Logs

## View Logs

```bash
docker compose logs
```

---

## Follow Logs

```bash
docker compose logs -f
```

---

## Django Logs

```bash
docker compose logs django
```

---

## PostgreSQL Logs

```bash
docker compose logs postgres
```

---

## Redis Logs

```bash
docker compose logs redis
```

---

## Nginx Logs

```bash
docker compose logs nginx
```

---

# Container Access

## Open Django Shell

```bash
docker compose exec django bash
```

---

## PostgreSQL Shell

```bash
docker compose exec postgres psql
```

---

## Redis CLI

```bash
docker compose exec redis redis-cli
```

---

# Health Verification

## Check Service Status

```bash
docker compose ps
```

Healthy services display:

```
Up (healthy)
```

---

## Inspect Container Health

```bash
docker inspect <container-name>
```

---

# Volume Management

## List Volumes

```bash
docker volume ls
```

---

## Remove Unused Volumes

```bash
docker volume prune
```

---

# Network Management

## List Networks

```bash
docker network ls
```

---

## Inspect Network

```bash
docker network inspect <network-name>
```

---

# Cleanup

## Remove Containers, Networks and Volumes

```bash
docker compose down -v
```

---

## Remove Unused Docker Resources

```bash
docker system prune
```

---

## Remove Everything Unused

```bash
docker system prune -a
```

> Use with caution. This removes unused images, containers, networks, and build cache.

---

# Common Workflow

Typical development workflow:

```text
Start Environment
        │
        ▼
Verify Containers
        │
        ▼
Develop Application
        │
        ▼
View Logs
        │
        ▼
Test Changes
        │
        ▼
Stop Environment
```

---

# Useful Tips

- Use `docker compose ps` to verify container health.
- Review logs before restarting containers.
- Rebuild images after changing Dockerfiles or dependencies.
- Use detached mode for long-running development sessions.
- Keep development and production configurations separate by using the appropriate Compose override file.

---

# Summary

This cheat sheet provides the most frequently used Docker Compose commands for DockForge.

It is intended as a quick operational reference during development, testing, and infrastructure management without replacing the detailed documentation found elsewhere in the project.