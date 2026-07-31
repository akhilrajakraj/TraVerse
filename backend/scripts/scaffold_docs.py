#!/usr/bin/env python3
"""
TraVerse Documentation Scaffold

Creates the complete documentation structure.

Run:

    python scripts/scaffold_docs.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS = PROJECT_ROOT / "docs"

# ---------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------

DIRECTORIES = [
    "implementation",
    "implementation/templates",
    "implementation/chapter-01",
    "implementation/chapter-02",

    "architecture",
    "architecture/workflows",
    "architecture/diagrams",
    "architecture/decisions",

    "engineering",

    "troubleshooting",

    "decisions",

    "api",

    "deployment",

    "testing",

    "references",
]

# ---------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------

FILES = [
    "README.md",

    "implementation/README.md",

    "implementation/templates/overview.template.md",
    "implementation/templates/implementation.template.md",
    "implementation/templates/validation.template.md",
    "implementation/templates/troubleshooting.template.md",
    "implementation/templates/lessons.template.md",
    "implementation/templates/checklist.template.md",

    "architecture/README.md",
    "architecture/system-overview.md",
    "architecture/application-map.md",
    "architecture/dependency-graph.md",

    "engineering/README.md",
    "engineering/onboarding.md",
    "engineering/coding-standards.md",
    "engineering/scripts.md",
    "engineering/best-practices.md",
    "engineering/lessons-learned.md",
    "engineering/glossary.md",

    "troubleshooting/README.md",
    "troubleshooting/django.md",
    "troubleshooting/docker.md",
    "troubleshooting/compose.md",
    "troubleshooting/postgres.md",
    "troubleshooting/redis.md",
    "troubleshooting/networking.md",
    "troubleshooting/git.md",

    "decisions/README.md",
    "decisions/ADR-template.md",
    "decisions/ADR-001-project-structure.md",
    "decisions/ADR-002-django-app-layout.md",

    "api/README.md",
    "api/authentication.md",
    "api/endpoints.md",
    "api/schemas.md",

    "deployment/README.md",
    "deployment/development.md",
    "deployment/staging.md",
    "deployment/production.md",

    "testing/README.md",
    "testing/unit-testing.md",
    "testing/integration-testing.md",
    "testing/api-testing.md",

    "references/README.md",
    "references/useful-links.md",
    "references/learning-resources.md",
    "references/terminology.md",
    "references/external-services.md",
]


def create_directory(path: Path) -> bool:
    if path.exists():
        return False
    path.mkdir(parents=True, exist_ok=True)
    return True


def create_file(path: Path) -> bool:
    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)

    title = path.stem.replace("-", " ").replace("_", " ").title()

    path.write_text(
        f"# {title}\n\n"
        "TODO: Add documentation.\n",
        encoding="utf-8",
    )

    return True


def main():

    print("=" * 65)
    print("TraVerse Documentation Scaffold")
    print("=" * 65)

    DOCS.mkdir(exist_ok=True)

    created_dirs = 0
    created_files = 0
    skipped = 0

    print("\nCreating directories...\n")

    for directory in DIRECTORIES:

        if create_directory(DOCS / directory):
            print(f"+ {directory}")
            created_dirs += 1
        else:
            print(f"✓ {directory}")
            skipped += 1

    print("\nCreating files...\n")

    for file in FILES:

        if create_file(DOCS / file):
            print(f"+ {file}")
            created_files += 1
        else:
            print(f"✓ {file}")
            skipped += 1

    print("\n" + "=" * 65)
    print("Documentation scaffold completed successfully.")
    print("=" * 65)
    print(f"Directories Created : {created_dirs}")
    print(f"Files Created       : {created_files}")
    print(f"Skipped             : {skipped}")
    print("=" * 65)


if __name__ == "__main__":
    main()
    