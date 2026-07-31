#!/usr/bin/env python3
"""
Fix all Django AppConfig files.

Run:
    python scripts/fix_app_configs.py
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "apps"

for app_dir in sorted(APPS_DIR.iterdir()):

    if not app_dir.is_dir():
        continue

    apps_py = app_dir / "apps.py"

    if not apps_py.exists():
        continue

    app = app_dir.name
    verbose = app.replace("_", " ").title()

    text = apps_py.read_text(encoding="utf-8")

    # Replace either single or double quoted names
    text = re.sub(
        r'name\s*=\s*[\'"][^\'"]+[\'"]',
        f'name = "apps.{app}"',
        text,
    )

    if "verbose_name" not in text:
        text = text.replace(
            f'name = "apps.{app}"',
            f'name = "apps.{app}"\n    verbose_name = "{verbose}"',
        )

    apps_py.write_text(text, encoding="utf-8")

    print(f"✓ {app}")

print("\nAll AppConfig files updated successfully.")