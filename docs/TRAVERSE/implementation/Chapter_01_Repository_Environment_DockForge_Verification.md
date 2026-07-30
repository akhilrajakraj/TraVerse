# Chapter 1 — Repository, Environment & DockForge Verification

**Volume 1: Foundations | Chapter 1 of 29**

> No application code is written in this chapter. This chapter exists to prove, beyond doubt, that the platform (DockForge) you are building on top of is alive, healthy, and correctly configured — before a single line of business logic touches it. Skipping this chapter is the single most common cause of "it works on my machine" disasters later.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Clone and correctly configure the DockForge-based repository without modifying any infrastructure file.
- Stand up the full stack (Django, Postgres, Redis, Nginx, Gunicorn) via Docker Compose.
- Prove — with commands and real output, not assumptions — that every platform service is reachable.
- Know exactly what "healthy" looks like, so that in later chapters you can instantly tell whether a bug is *your* application code or the *platform*.

---

## 2. Theory

### 2.1 What Is DockForge, Concretely? (ELI10)

Imagine DockForge as a fully furnished apartment you're renting. The electricity works, water runs, the front door lock works. You didn't build any of that — you just need to know **where the light switches are** and **how to check the lights actually turn on** before you move your furniture in.

DockForge gives you, already working:
- A `docker-compose.yml` that starts Postgres, Redis, Django (via Gunicorn), and Nginx together.
- A Django project with base settings already split into `dev`/`prod`.
- A `/health/` endpoint that reports whether the app can reach its dependencies.
- Logging already configured to write structured, readable logs.
- `.env.example` describing every environment variable the platform expects.

### 2.2 Why "Verification" Is Its Own Chapter, Not Just a Setup Step

In enterprise engineering, you never assume infrastructure works just because someone handed it to you. You **verify** it, the same way a pilot runs a pre-flight checklist even on a plane maintenance already certified as airworthy. If something is broken here, it is far cheaper to find out now (before any of your code exists) than in Chapter 12 when you're debugging an AI agent and can't tell if the failure is Redis, Celery, or your own code.

### 2.3 What "Healthy" Means Here

A platform is healthy when **all four** of these are simultaneously true:
1. All containers report `Up` (not `Restarting`, not `Exited`).
2. Django can open a connection to Postgres.
3. Django can open a connection to Redis.
4. The `/health/` endpoint returns HTTP `200` with a JSON body confirming both.

---

## 3. Architecture Decision

**Decision:** This chapter produces zero new files inside `apps/` or `ai/`. The only files touched are `.env` (created from `.env.example`, never committed) and, optionally, a throwaway verification script kept outside version control.

**Why:** Chapter 2 is where the actual `apps/` scaffold begins. Mixing scaffold work into verification work makes it impossible to know, if something breaks, whether the platform or your new scaffold is at fault. This is the same "one thing at a time" discipline stated in the Architecture Handbook §6.1.

---

## 4. Why Before How

Before you type a single command, understand **why each one exists**:

| Command family | Why it exists |
|---|---|
| `docker compose up` | Starts every service defined in `docker-compose.yml` in the correct dependency order (Postgres/Redis before Django, Django before Nginx) |
| `docker compose ps` | Lets you see container state without reading raw Docker internals |
| `docker compose logs` | The single most important debugging tool you will use for the entire project |
| `docker compose exec` | Runs a one-off command *inside* an already-running container, using that container's exact environment — never run Django commands on your host machine directly, because your host doesn't have the same Python/Postgres client libraries configured |

---

## 5. File Structure (What You Should See After Cloning, Before Any Edits)

```
project-root/
├── docker-compose.yml          # DockForge — do not edit
├── docker-compose.override.yml # DockForge dev overrides — do not edit
├── Dockerfile                  # DockForge — do not edit
├── nginx/
│   └── nginx.conf              # DockForge — do not edit
├── .env.example                # DockForge — template, safe to read, never edit values here
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── config/                     # DockForge's Django settings package (base.py, dev.py, prod.py)
├── manage.py
└── docs/
    └── (this Bible + Architecture Handbook live here going forward)
```

You should **not yet see** an `apps/` folder or an `ai/` folder — those arrive in Chapter 2 and Chapter 11 respectively. If you see them already, stop and confirm with your team whether someone has jumped ahead.

---

## 6. Folder Location

All commands in this chapter are run from `project-root/` (the folder containing `docker-compose.yml`). If you are anywhere else, `cd` there first. Nothing in this chapter is run from inside a container's shell manually — Compose does that for you.

---

## 7. Terminal Commands

### 7.1 Clone and Enter the Repository

```bash
git clone <your-dockforge-repo-url> ai-travel-planner
cd ai-travel-planner
```

### 7.2 Create Your Local Environment File

```bash
cp .env.example .env
```

**Why this exact command:** `.env.example` is committed to git and contains *safe placeholder* values and a list of every variable the platform needs. `.env` is your real, private file — it is already listed in `.gitignore` by DockForge. Never rename this the other way around.

### 7.3 Open `.env` and Fill In Real Values

At minimum, for this chapter, confirm these exist (values will be dummy/local for now — real secrets like `GROQ_API_KEY` aren't needed until Chapter 11):

```
DEBUG=True
SECRET_KEY=dev-only-insecure-key-change-in-prod
DATABASE_URL=postgres://postgres:postgres@db:5432/ai_travel_planner
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Why `db` and `redis` as hostnames, not `localhost`:** Inside Docker Compose's internal network, each service is reachable by its *service name* from `docker-compose.yml`, not `localhost`. This is a very common beginner confusion — `localhost` inside the Django container refers to the Django container itself, not your host machine or the database container.

---

## 8. Docker Commands

### 8.1 Build and Start Everything

```bash
docker compose up --build -d
```

- `--build`: forces Docker to rebuild the image from the `Dockerfile`, so you're not running a stale cached image on first run.
- `-d`: "detached" — runs in the background so your terminal isn't blocked.

### 8.2 Check Container Status

```bash
docker compose ps
```

**Expected output (shape, not exact values):**

```
NAME                        STATUS
ai-travel-planner-web-1     Up 12 seconds
ai-travel-planner-db-1      Up 14 seconds (healthy)
ai-travel-planner-redis-1   Up 14 seconds (healthy)
ai-travel-planner-nginx-1   Up 10 seconds
```

Every row must say `Up`. If you see `Restarting` or `Exited`, go to Section 13 (Debugging) before continuing.

### 8.3 Watch Logs Live (Especially on First Boot)

```bash
docker compose logs -f web
```

Press `Ctrl+C` to stop following (this does not stop the container, only the log stream).

---

## 9. Expected Output

### 9.1 Django Boot Log (via `docker compose logs web`)

```
web-1  | Watching for file changes with StatReloader
web-1  | Performing system checks...
web-1  |
web-1  | System check identified no issues (0 silenced).
web-1  | Django version 5.x, using settings 'config.settings.dev'
web-1  | Starting development server at http://0.0.0.0:8000/
```

### 9.2 Health Check Response

```bash
curl -i http://localhost:8000/health/
```

Expected:

```
HTTP/1.1 200 OK
Content-Type: application/json

{"status": "ok", "database": "ok", "redis": "ok"}
```

If `database` or `redis` shows `"error"` instead of `"ok"`, the containers are running but not actually reachable from Django — see Section 13.

---

## 10. Code

There is intentionally almost no code in this chapter — you are verifying, not building. The one artifact worth creating is a tiny, disposable verification script, kept outside of `apps/` since it belongs to no app:

```python
# scripts/verify_platform.py
"""
One-off platform verification script.
NOT part of the application layer. NOT imported by any Django app.
Safe to delete after Chapter 1 is complete — kept here only as a
repeatable sanity check you can re-run any time you suspect the
platform (not your code) is the problem.
"""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.db import connections
from django.db.utils import OperationalError
import redis


def check_database() -> bool:
    try:
        connections["default"].cursor()
        return True
    except OperationalError:
        return False


def check_redis() -> bool:
    try:
        url = os.environ["REDIS_URL"]
        client = redis.from_url(url)
        return client.ping()
    except Exception:
        return False


if __name__ == "__main__":
    db_ok = check_database()
    redis_ok = check_redis()

    print(f"Database reachable: {db_ok}")
    print(f"Redis reachable:    {redis_ok}")

    if not (db_ok and redis_ok):
        sys.exit(1)

    print("Platform verification passed.")
```

Run it with:

```bash
docker compose exec web python scripts/verify_platform.py
```

---

## 11. Code Walkthrough

- `os.environ.setdefault(...)` + `django.setup()`: this is the minimum needed to use Django's ORM and settings *outside* of `manage.py` — necessary because this script isn't a management command, it's a standalone sanity check.
- `check_database()`: opening a cursor is the cheapest possible way to force Django to actually attempt a connection, rather than just checking settings exist.
- `check_redis()`: uses the `redis` Python client directly (already a DockForge base dependency) and calls `.ping()`, the standard Redis liveness check.
- The script exits with a non-zero status code on failure — this matters later when you wire similar checks into CI (Chapter 28); a script that always exits `0` is useless as an automated gate.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` on `/health/` | Nginx or Gunicorn not fully started yet | Wait a few seconds, re-run `docker compose ps`; if still down, check logs |
| `django.db.utils.OperationalError: could not connect to server` | `DATABASE_URL` uses `localhost` instead of `db` | Fix `.env`, restart with `docker compose up -d` |
| `redis.exceptions.ConnectionError` | `REDIS_URL` malformed or Redis container not healthy | Check `docker compose ps` for redis's health status |
| Container shows `Exited (1)` | Usually a misconfigured `.env` value crashing Django on boot | `docker compose logs web` to see the actual traceback |
| `Bind for 0.0.0.0:8000 failed: port is already allocated` | Another process (often a previous run) already holds the port | `docker compose down` first, or stop the conflicting process |

---

## 13. Debugging

**Step-by-step debugging flow if any service is not healthy:**

```bash
# 1. See which container is unhealthy
docker compose ps

# 2. Read that container's logs specifically
docker compose logs <service-name>

# 3. If Django itself won't boot, get a shell inside the container
docker compose exec web sh

# 4. From inside, manually test Postgres connectivity
docker compose exec web python -c "import psycopg2; psycopg2.connect('dbname=ai_travel_planner user=postgres password=postgres host=db')"

# 5. From inside, manually test Redis connectivity
docker compose exec web python -c "import redis; print(redis.from_url('redis://redis:6379/0').ping())"

# 6. Nuclear reset if state is corrupted (destroys local dev DB volume!)
docker compose down -v
docker compose up --build -d
```

**Rollback strategy if something fails and you can't fix it quickly:** `docker compose down -v` followed by re-cloning `.env` from `.env.example` and rebuilding is always safe at this stage, because **no application data exists yet**. This is the cheapest possible point in the entire project to hit a full reset button — another reason this verification happens before any real code is written.

---

## 14. Testing

There is no Django test suite yet (no apps exist). The "test" for this chapter is the verification script from Section 10 passing, plus this manual checklist:

```bash
docker compose ps                              # all Up
curl -i http://localhost:8000/health/          # 200, status ok
docker compose exec web python scripts/verify_platform.py   # exits 0
```

All three must succeed before moving to Chapter 2.

---

## 15. Git Commit

At this stage, the only new file is `scripts/verify_platform.py` (and your local `.env`, which must **never** be committed — confirm it's in `.gitignore`, don't just assume).

```bash
git add scripts/verify_platform.py
git status   # confirm .env is NOT listed as staged
git commit -m "chore: add platform verification script (Chapter 1)

Confirms DockForge platform (Postgres, Redis, Django boot, /health/)
is reachable before any application-layer code is introduced.
No infrastructure files modified."
```

**Why commit something this small:** professional git history tells a story. A reviewer six months from now should be able to read your commit log and reconstruct the entire build order from Chapter 1 onward — that only works if you commit at meaningful, small checkpoints, not in one giant dump at the end.

---

## 16. Checklist

- [ ] Repository cloned, DockForge files untouched
- [ ] `.env` created from `.env.example`, never committed
- [ ] `docker compose up --build -d` runs without error
- [ ] `docker compose ps` shows all services `Up`
- [ ] `curl http://localhost:8000/health/` returns `200` with `"database": "ok", "redis": "ok"`
- [ ] `scripts/verify_platform.py` exits `0`
- [ ] Verification script committed with a clear, professional commit message
- [ ] No files under `apps/` or `ai/` exist yet (that's correct — they don't belong here)

---

## 17. Next Chapter Preview

**Chapter 2 — Django Project Skeleton & App Registration** begins the actual application layer: creating the empty `apps/` directory structure in the exact dependency order from Architecture Handbook §4, wiring each app into `INSTALLED_APPS`, and confirming `python manage.py check` passes with zero errors — all before a single model is defined. Say **"Continue to Chapter 2"** when ready.
