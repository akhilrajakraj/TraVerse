"""
scripts/verify_platform.py

DockForge Platform Verification Script
--------------------------------------

Purpose
-------
Verifies that the DockForge platform is healthy before any business
logic is developed.

This script validates:

✓ Django settings import
✓ Database connectivity
✓ Redis connectivity
✓ Environment configuration

This script is intentionally NOT part of the application layer.
It can be safely removed after Chapter 1, although it is recommended
to keep it for future infrastructure verification and CI pipelines.

Exit Codes
----------
0 -> Platform Healthy
1 -> Platform Verification Failed
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------
# Make project root importable
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ---------------------------------------------------------------------
# Configure Django
# ---------------------------------------------------------------------

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

try:
    import django

    django.setup()

except Exception as exc:
    print("❌ Failed to initialize Django")
    print(exc)
    sys.exit(1)

# ---------------------------------------------------------------------
# Django imports
# ---------------------------------------------------------------------

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

import redis

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def success(message: str) -> None:
    print(f"✅ {message}")


def failure(message: str) -> None:
    print(f"❌ {message}")


# ---------------------------------------------------------------------
# Environment Verification
# ---------------------------------------------------------------------


def verify_environment() -> bool:

    section("Environment")

    required = [
        "DJANGO_SECRET_KEY",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_DB",
    ]

    ok = True

    for variable in required:

        if os.getenv(variable):
            success(variable)

        else:
            failure(f"{variable} not configured")
            ok = False

    return ok


# ---------------------------------------------------------------------
# Database Verification
# ---------------------------------------------------------------------


def verify_database() -> bool:

    section("PostgreSQL")

    try:

        connection = connections["default"]

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        success("Database connection established")

        return True

    except OperationalError as exc:

        failure(str(exc))
        return False

    except Exception as exc:

        failure(str(exc))
        return False


# ---------------------------------------------------------------------
# Redis Verification
# ---------------------------------------------------------------------


def verify_redis() -> bool:

    section("Redis")

    try:

        host = os.getenv("REDIS_HOST", "redis")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))

        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            socket_connect_timeout=5,
        )

        client.ping()

        success(
            f"Connected to redis://{host}:{port}/{db}"
        )

        return True

    except Exception as exc:

        failure(str(exc))
        return False


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main() -> None:

    print()
    print("DockForge Platform Verification")
    print("-" * 60)

    environment = verify_environment()
    database = verify_database()
    redis_ok = verify_redis()

    print()
    print("-" * 60)

    if all([environment, database, redis_ok]):

        success("Platform verification PASSED")
        sys.exit(0)

    failure("Platform verification FAILED")
    sys.exit(1)


if __name__ == "__main__":
    main()