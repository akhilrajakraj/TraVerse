#!/usr/bin/env python3
"""
TraVerse Chapter 2 Scaffold

Run inside the Django container:

    python scripts/scaffold_apps.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APPS = [
    "core",
    "accounts",
    "travelers",
    "destinations",
    "trips",
    "planner",
    "itinerary",
    "ai",
    "chat",
    "documents",
    "notifications",
    "payments",
    "bookings",
    "analytics",
]


def run(command: list[str], cwd: Path) -> None:
    """Run a command and stop immediately if it fails."""

    result = subprocess.run(command, cwd=cwd)

    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:

    # Inside the container this resolves to /app
    project_root = Path(__file__).resolve().parent.parent

    manage_py = project_root / "manage.py"
    apps_root = project_root / "apps"

    if not manage_py.exists():
        raise SystemExit(f"manage.py not found: {manage_py}")

    apps_root.mkdir(exist_ok=True)

    print("=" * 60)
    print("TraVerse Chapter 2 Scaffold")
    print("=" * 60)

    for app in APPS:

        app_dir = apps_root / app

        # Skip only if the app is already scaffolded
        if (app_dir / "apps.py").exists():
            print(f"✓ {app:<15} already exists")
            continue

        app_dir.mkdir(parents=True, exist_ok=True)

        print(f"Creating {app:<15}")

        run(
            [
                "python",
                "manage.py",
                "startapp",
                app,
                f"apps/{app}",
            ],
            cwd=project_root,
        )

    print()
    print("Running Django check...")
    print()

    run(
        [
            "python",
            "manage.py",
            "check",
        ],
        cwd=project_root,
    )

    print()
    print("=" * 60)
    print("Chapter 2 - Application Creation Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()