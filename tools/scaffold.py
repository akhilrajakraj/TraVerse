#!/usr/bin/env python3
"""
DockForge Project Scaffolder

Creates the complete project directory structure safely.

Features
--------
- Safe to run multiple times (idempotent)
- Never overwrites existing files
- Never deletes user files
- Creates missing directories
- Creates placeholder .gitkeep files
- Creates missing root files
- Displays a professional summary report
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==========================================================
# DIRECTORY STRUCTURE (LOCKED)
# ==========================================================

DIRECTORIES: List[str] = [
    ".github/workflows",

    "backend",
    "backend/apps",
    "backend/config",
    "backend/requirements",
    "backend/scripts",

    "infrastructure",
    "infrastructure/compose",
    "infrastructure/docker",
    "infrastructure/docker/django",
    "infrastructure/docker/postgres",
    "infrastructure/docker/redis",
    "infrastructure/env",

    "docs",
    "docs/architecture",
    "docs/api",
    "docs/decisions",

    "tests",

    "tools",
]

# ==========================================================
# ROOT FILES
# ==========================================================

FILES: List[str] = [
    "README.md",
    ".gitignore",
    ".env.example",
    "LICENSE",
]

# ==========================================================
# REPORT
# ==========================================================

@dataclass
class Report:
    directories_created: int = 0
    directories_existing: int = 0
    files_created: int = 0
    files_existing: int = 0
    errors: int = 0


report = Report()

# ==========================================================
# HELPERS
# ==========================================================

def create_directory(directory: str) -> None:
    """Create a directory safely."""
    path = PROJECT_ROOT / directory

    try:
        if path.exists():
            print(f"[EXISTS ] {directory}")
            report.directories_existing += 1
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE ] {directory}")
            report.directories_created += 1

        gitkeep = path / ".gitkeep"

        if not gitkeep.exists():
            gitkeep.touch()

    except Exception as error:
        report.errors += 1
        print(f"[ERROR  ] {directory}")
        print(f"          {error}")


def create_file(filename: str) -> None:
    """Create a file safely."""
    path = PROJECT_ROOT / filename

    try:
        if path.exists():
            print(f"[EXISTS ] {filename}")
            report.files_existing += 1
        else:
            path.touch()
            print(f"[CREATE ] {filename}")
            report.files_created += 1

    except Exception as error:
        report.errors += 1
        print(f"[ERROR  ] {filename}")
        print(f"          {error}")


def print_report() -> None:
    print("\n" + "=" * 60)
    print("DockForge Scaffold Report")
    print("=" * 60)

    print(f"Directories Created : {report.directories_created}")
    print(f"Directories Existing: {report.directories_existing}")
    print(f"Files Created       : {report.files_created}")
    print(f"Files Existing      : {report.files_existing}")
    print(f"Errors              : {report.errors}")

    print("=" * 60)

    if report.errors == 0:
        print("✅ Scaffold completed successfully.")
    else:
        print("⚠️ Scaffold completed with errors.")


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    print("=" * 60)
    print("DockForge Project Scaffolder")
    print("=" * 60)

    for directory in DIRECTORIES:
        create_directory(directory)

    for file in FILES:
        create_file(file)

    print_report()


if __name__ == "__main__":
    main()