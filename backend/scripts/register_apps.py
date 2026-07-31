#!/usr/bin/env python3
"""
Register all TraVerse apps in config/settings.py

Run:
    python scripts/register_apps.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = PROJECT_ROOT / "config" / "settings.py"

APPS = [
    "apps.core",
    "apps.accounts",
    "apps.travelers",
    "apps.destinations",
    "apps.trips",
    "apps.planner",
    "apps.itinerary",
    "apps.ai",
    "apps.chat",
    "apps.documents",
    "apps.notifications",
    "apps.payments",
    "apps.bookings",
    "apps.analytics",
]

text = SETTINGS.read_text(encoding="utf-8")

start = text.find("INSTALLED_APPS = [")

if start == -1:
    raise SystemExit("INSTALLED_APPS not found.")

end = text.find("]", start)

block = text[start:end]

for app in APPS:
    if f'"{app}"' not in block and f"'{app}'" not in block:
        block += f'\n    "{app}",'

new_text = text[:start] + block + text[end:]

SETTINGS.write_text(new_text, encoding="utf-8")

print("✓ INSTALLED_APPS updated")