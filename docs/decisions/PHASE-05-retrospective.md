# Phase 5 Retrospective – Redis Integration

**Project:** DockForge

**Phase:** Phase 5 – Redis Integration

**Status:** Completed

---

# Purpose

This document records the complete engineering journey of integrating Redis into DockForge.

Unlike architectural documentation, this retrospective focuses on:

- Challenges encountered
- Root causes
- Solutions implemented
- Lessons learned
- Best practices discovered during development

Its purpose is to prevent future developers from repeating the same mistakes and to preserve the reasoning behind every debugging decision.

---

# Phase Objective

The objective of Phase 5 was to introduce Redis into DockForge as the application's caching layer.

At the end of the phase the application should:

- Run Redis inside Docker.
- Configure Redis using environment variables.
- Connect Django to Redis using the Cache Framework.
- Successfully communicate with Redis.
- Demonstrate caching through an HTTP endpoint.
- Verify the complete cache lifecycle.

---

# Development Timeline

The Redis integration was completed in the following order.

1. Redis Fundamentals
2. Redis Architecture
3. Docker Integration
4. Environment Configuration
5. Django Cache Configuration
6. Connectivity Testing
7. Cache Demonstration
8. Documentation

Following this structured workflow made debugging significantly easier because each step was verified before moving to the next.

---

# Challenge 1

## Problem

Docker Compose failed to start.

Example:

```text
no configuration file provided: not found
```

---

## Root Cause

The command was executed from the project root directory instead of the directory containing the Docker Compose file.

DockForge stores its Compose configuration inside:

```text
infrastructure/compose/
```

Docker could not locate the configuration file.

---

## Solution

Execute Docker Compose from the correct directory.

Example:

```bash
cd infrastructure/compose
docker compose up -d
```

Or explicitly specify the compose file.

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

---

## Lesson Learned

Docker searches for a Compose file in the current working directory unless a file is explicitly provided.

Always verify the current working directory before executing Docker commands.

---

# Challenge 2

## Problem

Redis needed to communicate with Django.

The question was:

Should Redis be installed directly on Windows or inside Docker?

---

## Root Cause

There are multiple valid deployment methods.

Choosing different approaches across development environments leads to inconsistent infrastructure.

---

## Solution

Run Redis inside Docker.

Benefits:

- Consistent environment
- Easy setup
- No operating system dependency
- Matches enterprise deployment practices

---

## Lesson Learned

Infrastructure should be containerized whenever practical.

Containers improve reproducibility and simplify onboarding for new developers.

---

# Challenge 3

## Problem

Understanding the relationship between PostgreSQL and Redis.

Initially it appeared that Redis might replace PostgreSQL.

---

## Root Cause

Both Redis and PostgreSQL store information.

Without understanding their responsibilities they appear similar.

---

## Solution

Separate responsibilities clearly.

PostgreSQL:

- Permanent storage
- Source of truth
- Relational database

Redis:

- Temporary storage
- Performance optimization
- Cache

---

## Lesson Learned

Never introduce new infrastructure without defining its responsibility.

Each technology should solve one specific problem.

---

# Challenge 4

## Problem

Choosing how Redis configuration should be stored.

Possible options included:

- Hardcoded values
- Configuration file
- Environment variables

---

## Root Cause

Hardcoded infrastructure values reduce portability.

Changing environments would require changing application code.

---

## Solution

Store Redis configuration inside:

```text
infrastructure/env/development.env
```

Read the values during application startup.

---

## Lesson Learned

Configuration belongs outside the application source code.

Environment variables improve flexibility and deployment consistency.

---

# Challenge 5

## Problem

Django raised:

```text
NameError: name 'env' is not defined
```

---

## Root Cause

The Redis configuration attempted to use:

```python
env(...)
```

However, DockForge was configured using:

```python
load_dotenv()
```

The project did not use the `django-environ` library.

Therefore, the `env()` function did not exist.

---

## Solution

Replace:

```python
env("REDIS_HOST")
```

with:

```python
os.getenv("REDIS_HOST")
```

The final configuration matched the environment-loading strategy already used throughout DockForge.

---

## Lesson Learned

When extending an existing project, always follow the established conventions.

Introducing a second configuration strategy increases complexity and creates unnecessary bugs.

Consistency is more valuable than personal preference.

---

# Challenge 6

## Problem

How could Redis integration be verified?

Simply starting Redis does not prove that Django can communicate with it.

---

## Root Cause

Infrastructure availability is different from application connectivity.

A running service does not guarantee successful communication.

---

## Solution

Perform practical verification.

Open the Django shell.

```bash
python backend/manage.py shell
```

Write data.

```python
cache.set("test_key", "Hello Redis!", timeout=60)
```

Read data.

```python
cache.get("test_key")
```

Successful read and write operations confirmed that the integration was functioning correctly.

---

## Lesson Learned

Never assume infrastructure works because it starts successfully.

Always perform functional testing.

---

# Challenge 7

## Problem

Demonstrating caching inside a real application.

Testing inside the Django shell proves connectivity but does not demonstrate actual application behavior.

---

## Root Cause

Infrastructure testing and application testing serve different purposes.

The shell verifies Redis.

An HTTP endpoint verifies application integration.

---

## Solution

Create a demonstration endpoint.

```text
/system-info/
```

The endpoint:

- Checks Redis.
- Returns cached data when available.
- Generates new data when necessary.
- Stores newly generated data in Redis.

This demonstrated the complete cache lifecycle.

---

## Lesson Learned

Testing should progress from simple verification to real-world usage.

A working application is the ultimate proof that the integration is correct.

---

# Major Concepts Learned

During Phase 5 the following concepts were understood.

## Redis

- In-memory database
- Key-value storage
- Extremely fast
- Temporary storage

---

## Caching

- Cache Hit
- Cache Miss
- Cache-Aside Pattern
- TTL (Time To Live)

---

## Docker

- Official Redis image
- Container networking
- Port mapping
- Infrastructure isolation

---

## Django

- Cache Framework
- django-redis
- Environment configuration
- HTTP cache integration

---

# Best Practices Discovered

The following engineering practices proved valuable.

- Verify every phase before continuing.
- Test infrastructure independently.
- Test application integration separately.
- Keep configuration outside source code.
- Use official Docker images.
- Maintain one configuration strategy.
- Document every important decision.
- Record debugging knowledge immediately.

---

# Final Outcome

At the conclusion of Phase 5 DockForge successfully achieved:

- Dockerized Redis deployment.
- Environment-based configuration.
- Django Cache Framework integration.
- Redis communication.
- Cache verification.
- HTTP cache demonstration.
- Professional documentation.
- Enterprise-ready project architecture.

Redis is now an integrated component of DockForge rather than an isolated technology.

---

# Reflection

Phase 5 was not simply about learning Redis.

It demonstrated an enterprise engineering workflow:

1. Learn the technology.
2. Understand the architecture.
3. Design the integration.
4. Implement the solution.
5. Verify functionality.
6. Debug problems.
7. Document everything.

Following this process produced a reliable implementation while also creating documentation that will benefit future development.

This retrospective serves as a permanent engineering record of the Redis integration and should be updated whenever Redis is significantly expanded in future phases.