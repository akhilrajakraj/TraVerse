# Docker Command Cheatsheet

**Project:** DockForge

**Category:** Cheatsheet

**Purpose:** Quick reference for Docker and Docker Compose commands used throughout the DockForge project.

---

# Introduction

Docker provides numerous commands for building, running, inspecting, and managing containers. During the development of DockForge, only a subset of these commands was required, but these commands form the foundation of day-to-day container development.

This cheatsheet groups commands by purpose, making it easy to locate the right command during development or debugging.

---

# Docker vs Docker Compose

| Docker | Docker Compose |
|---------|----------------|
| Manages individual containers | Manages multiple containers together |
| One command per container | One command for the entire application |
| Suitable for simple workloads | Suitable for multi-service applications |

---

# Build Commands

## Build an Image

```bash
docker build -t image-name .
```

Builds a Docker image from the current directory.

Example:

```bash
docker build -t dockforge-backend .
```

---

## Build Using Docker Compose

```bash
docker compose build
```

Builds all services defined in the Compose file.

---

## Build Without Cache

```bash
docker compose build --no-cache
```

Forces Docker to rebuild every layer.

Useful after dependency or Dockerfile changes.

---

# Starting Services

## Start All Services

```bash
docker compose up
```

Starts all services.

---

## Start in Detached Mode

```bash
docker compose up -d
```

Runs containers in the background.

---

## Build and Start

```bash
docker compose up --build -d
```

Rebuilds images before starting services.

This was the most commonly used command during Phase 6.

---

# Stopping Services

## Stop Services

```bash
docker compose stop
```

Stops containers without removing them.

---

## Stop and Remove Everything

```bash
docker compose down
```

Stops and removes:

- Containers
- Networks

Volumes remain intact.

---

## Remove Volumes Too

```bash
docker compose down -v
```

Removes:

- Containers
- Networks
- Volumes

⚠️ This deletes persistent database data.

---

# Container Status

## List Running Containers

```bash
docker ps
```

Shows currently running containers.

---

## List All Containers

```bash
docker ps -a
```

Includes stopped containers.

---

## Compose Service Status

```bash
docker compose ps
```

Displays the status of every service defined in the Compose file.

---

# Viewing Logs

## View All Logs

```bash
docker compose logs
```

Displays logs for all services.

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

## Follow Logs

```bash
docker compose logs -f django
```

Continuously streams logs.

Press:

```
Ctrl + C
```

to stop following.

---

# Executing Commands Inside Containers

## Open Bash

```bash
docker compose exec django bash
```

Starts a shell inside the Django container.

---

## Django Management Commands

Run migrations.

```bash
docker compose exec django python manage.py migrate
```

Create a superuser.

```bash
docker compose exec django python manage.py createsuperuser
```

Open Django shell.

```bash
docker compose exec django python manage.py shell
```

---

# Image Management

## List Images

```bash
docker images
```

---

## Remove an Image

```bash
docker rmi image-name
```

---

## Remove Unused Images

```bash
docker image prune
```

---

# Container Management

## Stop a Container

```bash
docker stop container-name
```

---

## Start a Container

```bash
docker start container-name
```

---

## Restart a Container

```bash
docker restart container-name
```

---

## Remove a Container

```bash
docker rm container-name
```

---

# Network Commands

## List Networks

```bash
docker network ls
```

---

## Inspect a Network

```bash
docker network inspect network-name
```

Example:

```bash
docker network inspect dockforge-network
```

---

# Volume Commands

## List Volumes

```bash
docker volume ls
```

---

## Inspect a Volume

```bash
docker volume inspect volume-name
```

---

## Remove a Volume

```bash
docker volume rm volume-name
```

---

# System Cleanup

## Remove Unused Containers

```bash
docker container prune
```

---

## Remove Unused Networks

```bash
docker network prune
```

---

## Remove Unused Volumes

```bash
docker volume prune
```

---

## Remove Everything Unused

```bash
docker system prune
```

---

## Complete Cleanup

```bash
docker system prune -a
```

⚠️ Removes unused images, containers, networks, and build cache.

Use carefully.

---

# Inspect Commands

## Inspect a Container

```bash
docker inspect container-name
```

Displays detailed container information.

---

## View Container Processes

```bash
docker top container-name
```

---

## View Resource Usage

```bash
docker stats
```

Shows live CPU and memory usage.

---

# Useful Development Workflow

## First-Time Setup

```bash
docker compose up --build -d
```

---

## Daily Development

```bash
docker compose up -d
```

---

## Check Services

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs django
```

---

## Stop Everything

```bash
docker compose down
```

---

# Common Debugging Workflow

When something goes wrong, follow this order:

```text
1. docker compose ps

↓

2. docker compose logs django

↓

3. docker compose logs postgres

↓

4. docker compose logs redis

↓

5. docker compose config

↓

6. docker compose up --build -d
```

This systematic approach helps isolate issues efficiently.

---

# Frequently Used Commands During Phase 6

| Command | Purpose |
|---------|---------|
| `docker compose up --build -d` | Build and start all services |
| `docker compose down` | Stop and remove containers |
| `docker compose ps` | Check service status |
| `docker compose logs django` | View Django logs |
| `docker compose logs postgres` | View PostgreSQL logs |
| `docker compose logs redis` | View Redis logs |
| `docker compose config` | Validate Compose configuration |
| `docker network ls` | List Docker networks |
| `docker volume ls` | List Docker volumes |
| `docker stats` | Monitor resource usage |

---

# Best Practices

- Use Docker Compose for multi-service applications.
- Rebuild images after changing dependencies or the Dockerfile.
- Review logs before making changes.
- Keep environment variables outside the source code.
- Use named volumes for persistent data.
- Prefer service names over `localhost` inside containers.
- Validate the Compose configuration before debugging complex issues.

---

# Conclusion

This cheatsheet summarizes the Docker and Docker Compose commands used throughout Phase 6 of DockForge. It is intended to serve as a quick reference during future phases of development, reducing the need to search for commonly used commands while reinforcing best practices for containerized backend development.