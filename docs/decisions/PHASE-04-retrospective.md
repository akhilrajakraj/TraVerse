# Phase 4 Retrospective: PostgreSQL Integration

## Status

Completed

---

## Phase Goal

Replace Django's default SQLite database with PostgreSQL running inside Docker while following enterprise development practices.

The objective was not only to connect Django to PostgreSQL but also to understand the complete infrastructure involved in a production-style backend environment.

---

# Timeline of the Phase

The PostgreSQL integration was completed through several milestones:

1. Install the PostgreSQL driver (`psycopg`)
2. Configure environment variables
3. Create a PostgreSQL Docker container
4. Configure persistent Docker volumes
5. Connect Django to PostgreSQL
6. Run database migrations
7. Verify successful database communication

Although the implementation itself was straightforward, several infrastructure-related issues were encountered during development.

Each issue provided valuable learning experience.

---

# Issue 1 — Docker Engine Was Not Running

## Symptom

Docker commands failed immediately.

Example:

```
Cannot connect to the Docker daemon
```

## Root Cause

Docker Desktop was not running.

The Docker CLI is only a client.

Without Docker Engine running, containers cannot be created or managed.

## Solution

Started Docker Desktop before executing Docker Compose commands.

## Lesson Learned

Always verify Docker Engine before debugging containers.

Useful commands:

```bash
docker version
docker info
```

---

# Issue 2 — Port 5432 Already Allocated

## Symptom

Docker Compose failed while creating PostgreSQL.

Example:

```
Bind for 0.0.0.0:5432 failed
```

## Root Cause

Another PostgreSQL instance was already using port 5432.

At different stages this included:

- a previous Docker PostgreSQL container
- a Windows PostgreSQL service

## Solution

Identified the conflicting process.

Stopped the unnecessary PostgreSQL instance before recreating the container.

Useful commands:

```bash
docker ps
netstat -ano | findstr :5432
```

## Lesson Learned

When Docker reports a port conflict, identify the process using the port before changing configuration.

---

# Issue 3 — Hostname "postgres" Could Not Be Resolved

## Symptom

Django reported:

```
could not translate host name "postgres"
```

## Root Cause

The Django application was running directly on Windows using `manage.py`.

The hostname `postgres` only exists inside Docker's internal network.

## Solution

Changed the development environment configuration:

```
POSTGRES_HOST=localhost
```

The hostname `postgres` will be used later when Django itself runs inside Docker.

## Lesson Learned

The correct hostname depends on where the application is running.

| Django Location | Database Host |
|-----------------|---------------|
| Windows | localhost |
| Docker Container | postgres |

---

# Issue 4 — Role "dockforge_user" Does Not Exist

## Symptom

Django failed to authenticate:

```
FATAL: role "dockforge_user" does not exist
```

## Initial Assumption

The PostgreSQL container had not created the expected database user.

## Investigation

Connected directly to PostgreSQL.

Executed:

```sql
\du
\l
```

The user existed.

The database also existed.

## Root Cause

Django was communicating with the wrong PostgreSQL server.

Windows PostgreSQL was answering requests instead of the Docker container.

## Solution

Stopped the Windows PostgreSQL service.

Verified that Docker PostgreSQL became the active database server.

## Lesson Learned

Never assume an application is communicating with the expected database.

Always verify.

---

# Issue 5 — Docker Port Was Not Published

## Symptom

```
docker port dockforge-postgres
```

returned no output.

The container was running, but Windows could not connect.

## Investigation

`docker compose config` correctly showed:

```yaml
ports:
  - "5432:5432"
```

However,

```
docker ps
```

displayed only:

```
5432/tcp
```

instead of

```
0.0.0.0:5432->5432/tcp
```

## Root Cause

The existing container had not been recreated with the updated networking configuration.

## Solution

Recreated the container:

```bash
docker compose down
docker compose up -d --force-recreate
```

## Lesson Learned

A running Docker container is a snapshot of the configuration that existed when it was created.

Changing `docker-compose.yml` does not automatically update existing containers.

---

# Issue 6 — Understanding Docker Volumes

During debugging it became clear that PostgreSQL stores its database inside a Docker volume.

Removing the container does not automatically remove database data.

The project used:

```
compose_postgres_data
```

This allows database persistence across container recreation.

## Lesson Learned

Containers are temporary.

Volumes are persistent.

Application data belongs in volumes, not inside containers.

---

# Key Commands Learned

Docker

```bash
docker ps
docker logs
docker inspect
docker port
docker exec
docker volume ls
docker compose config
docker compose down
docker compose up
docker compose up --force-recreate
```

PostgreSQL

```sql
\du
\l
\dt
```

Django

```bash
python backend/manage.py showmigrations
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

---

# Engineering Lessons

This phase reinforced several important engineering principles.

- Infrastructure problems should be investigated methodically rather than solved by trial and error.
- Always verify whether the application is communicating with the expected service.
- Read logs before making changes.
- Validate assumptions using inspection commands.
- Understand the difference between configuration files and runtime state.
- Use Docker volumes for persistent application data.
- Separate application configuration from application code.

---

# Outcome

Phase 4 successfully replaced SQLite with PostgreSQL.

DockForge now uses:

- PostgreSQL 17
- Docker Compose
- Persistent Docker volumes
- Environment-based configuration
- Django ORM with PostgreSQL
- Production-style database architecture

The project is now ready for Redis integration in Phase 5.

---

# Final Reflection

The greatest outcome of this phase was not connecting Django to PostgreSQL.

It was learning how to diagnose infrastructure problems systematically.

The debugging process provided practical experience with Docker networking, PostgreSQL administration, container lifecycle, environment configuration, and service isolation.

These are foundational skills for enterprise backend development and will continue to be used throughout the remaining phases of DockForge.