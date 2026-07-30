# Redis Integration Architecture

**Project:** DockForge  
**Phase:** Phase 5 – Redis Integration  
**Document Version:** 1.0  
**Status:** Completed

---

# Purpose

This document explains the complete Redis integration performed in DockForge.

It is intended for:

- Beginners learning Redis for the first time.
- Developers contributing to DockForge.
- Future maintainers who need to understand why Redis was introduced.
- Anyone wanting to understand the complete Redis integration process from architecture to implementation.

Unlike a tutorial, this document explains not only **how Redis was integrated**, but also **why it was required**, **how it works internally**, and **how it fits into DockForge's architecture**.

---

# Table of Contents

1. Introduction
2. What is Redis?
3. Why Does DockForge Need Redis?
4. Redis vs PostgreSQL
5. Understanding Caching
6. Cache Hit vs Cache Miss
7. Redis Architecture in DockForge
8. Summary

---

# 1. Introduction

Before Redis was introduced, DockForge already had a fully working PostgreSQL database.

The application architecture looked like this:

```text
                 Browser
                    │
                    ▼
              Django Backend
                    │
                    ▼
               PostgreSQL
```

Whenever a client requested data, Django queried PostgreSQL.

This architecture works perfectly.

However, as the number of users grows, the database begins performing the same queries repeatedly.

For example:

- User opens Dashboard
- User refreshes Dashboard
- Another user opens Dashboard
- Another refresh occurs

Although the information may not have changed, PostgreSQL executes the same query every time.

This repeated work increases:

- Database load
- CPU usage
- Disk operations
- Response time

Large-scale applications solve this problem by introducing a caching layer.

That caching layer is Redis.

---

# 2. What is Redis?

Redis stands for:

**REmote DIctionary Server**

Redis is an **in-memory key-value data store**.

Unlike traditional databases that primarily store information on disk, Redis stores information in RAM.

Because RAM is significantly faster than disk storage, Redis can return information extremely quickly.

Think of Redis as an extremely fast dictionary.

Example:

Key

```text
user:1
```

Value

```json
{
    "name": "Akhil",
    "email": "akhil@example.com"
}
```

Instead of executing SQL queries, Redis retrieves information using keys.

Example:

```text
GET user:1
```

Redis immediately returns the associated value.

This makes Redis ideal for storing temporary information that needs to be accessed very quickly.

---

# 3. Why Does DockForge Need Redis?

To understand Redis, first understand the problem.

Imagine a college library.

There is one librarian.

Every student asks for the same textbook.

Without Redis:

Student 1

↓

Librarian walks to storage

↓

Returns with book

Student 2

↓

Librarian walks again

↓

Returns with book

Student 3

↓

Librarian repeats the same work

The same task is performed repeatedly.

PostgreSQL behaves similarly.

Even if the requested information has not changed, PostgreSQL still executes the query.

Redis solves this problem.

Instead of repeatedly visiting storage, the librarian keeps frequently requested books on the front desk.

Now the process becomes:

Student

↓

Front Desk

↓

Book Found

↓

Done

Redis acts as that front desk.

It stores frequently accessed information temporarily so that PostgreSQL does not have to repeat the same work.

---

# 4. Redis vs PostgreSQL

Many beginners believe Redis replaces PostgreSQL.

This is incorrect.

Redis and PostgreSQL have different responsibilities.

| PostgreSQL | Redis |
|------------|-------|
| Primary database | Cache |
| Persistent storage | Temporary storage |
| Stores data on disk | Stores data in RAM |
| Uses SQL | Uses key-value pairs |
| Source of truth | Performance optimization |

PostgreSQL permanently stores application data.

Redis temporarily stores frequently requested data.

If Redis is cleared, the application still works because PostgreSQL still contains the original data.

If PostgreSQL is lost, Redis cannot rebuild the application data.

Therefore:

**PostgreSQL is the source of truth.**

Redis is a performance layer.

---

# 5. Understanding Caching

Caching means storing frequently requested information somewhere faster.

Without caching:

```text
Browser
    │
    ▼
Django
    │
    ▼
PostgreSQL
    │
    ▼
Return Response
```

Every request reaches PostgreSQL.

With Redis:

```text
Browser
    │
    ▼
Django
    │
    ▼
Redis
```

If Redis already contains the requested information:

```text
Return Cached Response
```

No database query is required.

This significantly reduces:

- Database workload
- Query execution time
- Server response time

Caching improves overall application performance.

---

# 6. Cache Hit vs Cache Miss

Understanding these two concepts is essential.

## Cache Miss

A Cache Miss occurs when Redis does not contain the requested data.

Flow:

```text
Browser

↓

Django

↓

Redis

↓

Data Not Found

↓

PostgreSQL

↓

Generate Response

↓

Store in Redis

↓

Return Response
```

The first request is usually a Cache Miss.

---

## Cache Hit

A Cache Hit occurs when Redis already contains the requested information.

Flow:

```text
Browser

↓

Django

↓

Redis

↓

Data Found

↓

Return Immediately
```

No SQL query is executed.

This is the primary purpose of Redis.

---

# 7. Redis Architecture in DockForge

After Redis integration, DockForge follows this architecture:

```text
                     Browser
                        │
                        ▼
                  Django Backend
                        │
                        ▼
              Django Cache Framework
                        │
                        ▼
                 django-redis Backend
                        │
                        ▼
                     Redis Server
                        │
             (Only on Cache Miss)
                        ▼
                   PostgreSQL
```

Notice that PostgreSQL has not been removed.

Redis acts as an additional layer between Django and PostgreSQL.

Whenever possible, Django retrieves information from Redis.

Only when Redis does not contain the requested information does Django communicate with PostgreSQL.

---

# 8. Summary

At the end of this section, the following concepts should be understood:

- Redis is an in-memory key-value database.
- Redis is significantly faster than PostgreSQL because it stores data in RAM.
- Redis does not replace PostgreSQL.
- PostgreSQL remains the primary database.
- Redis is used for caching.
- Caching improves application performance.
- Cache Hits are fast.
- Cache Misses require PostgreSQL queries.
- Redis reduces unnecessary database workload.

The next section explains how Redis was integrated into DockForge using Docker, environment variables, and Django's Cache Framework.

---

# 9. Docker Integration

## Why Run Redis Inside Docker?

Redis can be installed directly on the operating system or inside a Docker container.

For DockForge, Redis was deployed using Docker.

Reasons:

- Keeps the development environment isolated.
- Easy to start and stop.
- Consistent across all developers' machines.
- No manual installation required.
- Matches modern enterprise deployment practices.

Instead of installing Redis directly on Windows, Docker manages the Redis server.

This means every developer working on DockForge will have the exact same Redis environment.

---

## Docker Architecture

After Redis integration, Docker manages two infrastructure services.

```text
Docker Engine
│
├── PostgreSQL Container
│
└── Redis Container
```

The Django application communicates with these services through their exposed ports.

---

## Redis Docker Image

DockForge uses the official Redis Docker image.

```yaml
redis:
  image: redis:8-alpine
```

### Why the Official Image?

The official Redis image is maintained by the Redis team.

Benefits include:

- Stable releases
- Security updates
- Small image size
- Production-ready
- Widely used by enterprises

No custom Dockerfile was required because Redis does not need additional software for our current use case.

---

## Why Use Alpine?

The image:

```text
redis:8-alpine
```

uses Alpine Linux.

Advantages:

- Smaller download size
- Faster startup
- Reduced storage usage
- Lower attack surface

For development and production environments, Alpine is an excellent choice unless additional operating system packages are required.

---

## Docker Compose Configuration

Redis was added as a new service inside:

```text
infrastructure/compose/docker-compose.yml
```

Configuration:

```yaml
redis:
  image: redis:8-alpine
  container_name: dockforge-redis
  restart: unless-stopped
  ports:
    - "6379:6379"
```

---

## Understanding Each Configuration

### image

```yaml
image: redis:8-alpine
```

Tells Docker which Redis image to download and run.

---

### container_name

```yaml
container_name: dockforge-redis
```

Assigns a human-readable name to the container.

Without this, Docker would generate a random container name.

---

### restart

```yaml
restart: unless-stopped
```

Automatically restarts Redis if:

- Docker restarts
- The computer reboots
- The Redis process crashes

This improves service reliability.

---

### ports

```yaml
6379:6379
```

The format is:

```text
HOST_PORT : CONTAINER_PORT
```

Meaning:

Windows

↓

Port 6379

↓

Docker Container

↓

Redis

This allows Django running on Windows to communicate with Redis inside Docker.

---

# 10. Environment Configuration

Applications should never hardcode infrastructure configuration.

Instead of writing:

```python
REDIS_HOST = "localhost"
```

the values are stored inside environment files.

DockForge stores Redis configuration inside:

```text
infrastructure/env/development.env
```

Configuration:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## Why Use Environment Variables?

Imagine moving DockForge to another server.

Development:

```text
localhost
```

Docker:

```text
redis
```

Production:

```text
redis.company.internal
```

If these values were hardcoded, the application code would need to change.

Instead, only the environment variables change.

The application code remains exactly the same.

This follows one of the core principles of modern backend development:

> Configuration belongs outside the application code.

---

## Understanding Each Variable

### REDIS_HOST

Specifies where the Redis server is running.

Development:

```text
localhost
```

Dockerized Django (future):

```text
redis
```

---

### REDIS_PORT

Specifies which network port Redis is listening on.

Default:

```text
6379
```

---

### REDIS_DB

Redis supports multiple logical databases.

Example:

```text
Redis Server

├── Database 0
├── Database 1
├── Database 2
└── Database 3
```

DockForge currently uses:

```text
Database 0
```

This is the default Redis database.

---

# 11. Django Cache Framework

Simply running Redis is not enough.

Django needs a way to communicate with Redis.

Instead of directly sending Redis commands, Django uses its built-in Cache Framework.

Architecture:

```text
Django Application
        │
        ▼
Cache Framework
        │
        ▼
django-redis Backend
        │
        ▼
Redis Server
```

The Cache Framework provides a common interface.

This means Django could use:

- Redis
- Memcached
- Local Memory Cache
- Database Cache

without changing application code.

Only the backend configuration changes.

---

# 12. Why We Used django-redis

Two Python packages are commonly confused.

## Package 1

```text
redis
```

Purpose:

General-purpose Redis client.

Developers manually write Redis commands.

Example:

```python
import redis

client = redis.Redis(...)
client.get(...)
client.set(...)
```

This gives complete control but requires more code.

---

## Package 2

```text
django-redis
```

Purpose:

Integrates Redis directly into Django's Cache Framework.

Instead of creating Redis clients manually, Django provides:

```python
cache.get(...)
cache.set(...)
```

Advantages:

- Cleaner code
- Native Django integration
- Easy configuration
- Recommended for Django projects

For DockForge, this is the appropriate choice.

---

# 13. Django Cache Configuration

Redis was connected to Django using the following configuration.

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": (
            f"redis://{os.getenv('REDIS_HOST')}:"
            f"{os.getenv('REDIS_PORT')}/"
            f"{os.getenv('REDIS_DB')}"
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
```

---

## Understanding the Configuration

### default

Django supports multiple cache backends.

DockForge currently uses one default cache.

---

### BACKEND

Specifies which cache implementation Django should use.

Value:

```text
django_redis.cache.RedisCache
```

This tells Django to use Redis.

---

### LOCATION

Specifies where Redis is running.

Example:

```text
redis://localhost:6379/0
```

Breaking this down:

Protocol

```text
redis://
```

Host

```text
localhost
```

Port

```text
6379
```

Logical Database

```text
0
```

Together, these form the complete Redis connection URL.

---

### OPTIONS

Additional backend-specific configuration.

DockForge uses:

```python
CLIENT_CLASS = "django_redis.client.DefaultClient"
```

This is the recommended client for standard Redis cache operations.

---

# 14. Redis Communication Flow

When Django stores information:

```python
cache.set("system_info", data)
```

The request flows through multiple layers.

```text
Application

↓

Django Cache API

↓

django-redis

↓

Redis Server

↓

Store Data
```

When Django retrieves information:

```python
cache.get("system_info")
```

Flow:

```text
Application

↓

Django Cache API

↓

Redis Server

↓

Return Cached Value
```

Notice that the application never communicates directly with Redis.

The Cache Framework manages all communication.

---

# 15. Summary

After completing this phase, DockForge successfully achieved:

- Dockerized Redis deployment.
- Official Redis Docker image.
- Environment-based Redis configuration.
- Django Cache Framework integration.
- django-redis backend configuration.
- Communication between Django and Redis.
- Enterprise-ready configuration using environment variables.

The next section documents the complete verification process, cache demonstration, troubleshooting steps, lessons learned, and future enhancements.

---

# 16. Verification Process

Implementing Redis is only half of the work.

The other half is verifying that the integration functions correctly.

Enterprise software development always includes a verification phase before considering a feature complete.

The following verification steps were performed during Redis integration.

---

## Step 1 — Verify Docker Containers

The first step was confirming that both PostgreSQL and Redis containers were running.

Command:

```bash
docker ps
```

Expected Result:

```text
CONTAINER ID   IMAGE              NAME
xxxxxxxxxxxx   postgres:17        dockforge-postgres
xxxxxxxxxxxx   redis:8-alpine     dockforge-redis
```

This confirms that the infrastructure services are running.

---

## Step 2 — Verify Django Configuration

Command:

```bash
python backend/manage.py check
```

Expected Output:

```text
System check identified no issues (0 silenced).
```

This verifies that Django's configuration is valid.

It does **not** verify Redis communication.

It only verifies that the project configuration contains no errors.

---

## Step 3 — Verify Cache Communication

Open the Django shell.

```bash
python backend/manage.py shell
```

Import Django's cache framework.

```python
from django.core.cache import cache
```

Store a value.

```python
cache.set("test_key", "Hello Redis!", timeout=60)
```

Expected Output:

```python
True
```

Retrieve the value.

```python
cache.get("test_key")
```

Expected Output:

```python
'Hello Redis!'
```

This confirms that:

- Django can communicate with Redis.
- Redis accepts write operations.
- Redis successfully returns stored values.

---

## Step 4 — Verify Through an HTTP Request

A demonstration endpoint was created.

```text
/system-info/
```

Purpose:

Demonstrate Redis caching through an actual HTTP request.

---

First Request

Redis does not contain cached data.

Response:

```json
{
    "source": "Fresh Response",
    "data": {
        "message": "DockForge Redis is working!",
        "generated_at": "2026-07-26T18:31:02.383098+00:00"
    }
}
```

The response is generated by Django.

Redis then stores the generated data.

---

Second Request

Redis already contains the data.

Response:

```json
{
    "source": "Redis Cache",
    "data": {
        "message": "DockForge Redis is working!",
        "generated_at": "2026-07-26T18:31:02.383098+00:00"
    }
}
```

Notice that the timestamp remains unchanged.

This proves the response came directly from Redis rather than being regenerated.

---

## Cache Lifecycle

The complete cache lifecycle is shown below.

```text
Request

↓

Redis

↓

Cache Hit?

↓

YES
│
└── Return Cached Response

NO
│
└── Generate Data
      │
      ▼
Store in Redis
      │
      ▼
Return Response
```

This pattern is commonly known as the **Cache-Aside Pattern** and is one of the most widely used caching strategies in backend systems.

---

# 17. Challenges Encountered

Every engineering project involves debugging.

The following issues were encountered during Redis integration.

---

## Challenge 1

### Problem

```text
NameError: name 'env' is not defined
```

---

### Cause

The Redis configuration initially used:

```python
env("REDIS_HOST")
```

However, DockForge uses:

```python
load_dotenv()
```

instead of the `django-environ` library.

Therefore, no `env()` object existed.

---

### Solution

Replace:

```python
env(...)
```

with:

```python
os.getenv(...)
```

Example:

```python
os.getenv("REDIS_HOST")
```

---

### Lesson Learned

Always use the same environment-loading strategy throughout the project.

Mixing different configuration libraries creates unnecessary errors and inconsistent code.

---

## Challenge 2

### Problem

How should Redis be tested?

---

### Cause

Successfully configuring Redis does not guarantee that Django can communicate with it.

---

### Solution

Instead of assuming the integration worked, perform an actual write and read operation.

```python
cache.set(...)
cache.get(...)
```

Only after successful read/write operations can the integration be considered complete.

---

### Lesson Learned

Configuration validation is not the same as functional verification.

Always perform practical integration testing.

---

# 18. Lessons Learned

During this phase, the following concepts were learned.

- Redis is an in-memory key-value database.
- Redis complements PostgreSQL rather than replacing it.
- Docker simplifies infrastructure management.
- Environment variables improve application portability.
- Django communicates with Redis through the Cache Framework.
- django-redis integrates Redis with Django.
- Cache Hits improve performance.
- Cache Misses retrieve fresh data.
- TTL automatically expires cached data.
- Infrastructure should always be verified through testing rather than assumption.

---

# 19. Best Practices

The following practices were followed during Redis integration.

---

## Use Official Docker Images

Always prefer official Docker images unless customization is required.

Advantages:

- Reliable
- Secure
- Well maintained
- Community supported

---

## Keep Configuration Outside Source Code

Avoid hardcoding:

```python
REDIS_HOST = "localhost"
```

Instead, use environment variables.

Benefits:

- Easier deployment
- Better security
- Greater flexibility
- Cleaner code

---

## Verify Every Infrastructure Component

Never assume a service works simply because it starts.

Always verify:

- Service availability
- Network communication
- Application integration
- Functional behavior

---

## Separate Responsibilities

Redis should be responsible for performance optimization.

PostgreSQL should remain the permanent source of application data.

Each technology should have a clearly defined responsibility.

---

# 20. Future Enhancements

The current Redis implementation focuses only on caching.

Future phases of DockForge may use Redis for additional enterprise features.

Examples include:

- User session storage
- Background job queues
- Celery workers
- Rate limiting
- OTP verification
- Temporary authentication tokens
- Notification systems
- Real-time event processing

Redis provides the foundation for these advanced capabilities.

---

# 21. Conclusion

Redis has been successfully integrated into DockForge.

The project now includes:

- Dockerized Redis infrastructure.
- Environment-based configuration.
- Django Cache Framework integration.
- django-redis backend.
- Functional cache implementation.
- Verified Redis communication.
- HTTP cache demonstration.
- Enterprise-ready project structure.

More importantly, this phase established an understanding of **why caching exists**, **how Redis works**, **how Django communicates with Redis**, and **how Redis improves application performance**.

This knowledge will be reused throughout future phases of DockForge as additional enterprise features are implemented.

---

# Key Takeaways

By completing this phase, the following concepts have been mastered.

✅ What Redis is.

✅ Why caching is important.

✅ Difference between Redis and PostgreSQL.

✅ Docker-based Redis deployment.

✅ Environment variable configuration.

✅ Django Cache Framework.

✅ django-redis integration.

✅ Cache Hit and Cache Miss.

✅ Cache-Aside Pattern.

✅ TTL (Time To Live).

✅ Redis verification techniques.

✅ Enterprise infrastructure practices.

Redis is no longer just another technology added to DockForge.

It is now an integral part of the application's architecture and serves as the foundation for future scalability, performance optimization, and distributed system capabilities.