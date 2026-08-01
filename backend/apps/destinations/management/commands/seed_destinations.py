"""
Seeds the destination catalog from a JSON fixture.

The command is safe to execute multiple times because it uses
update_or_create() rather than create().
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.destinations.models import Destination


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "destinations_seed.json"
)


class Command(BaseCommand):
    """
    Seed the destinations catalog.
    """

    help = (
        "Seed the destinations catalog "
        "from fixtures/destinations_seed.json"
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )

    def handle(self, *args, **options):

        dry_run = options["dry_run"]

        data = json.loads(
            FIXTURE_PATH.read_text(
                encoding="utf-8",
            )
        )

        created = 0
        updated = 0

        self.stdout.write("Seeding destinations...")

        for entry in data:

            if dry_run:

                self.stdout.write(
                    f"Would upsert: "
                    f"{entry['name']}, "
                    f"{entry['country']}"
                )

                continue

            _, was_created = Destination.objects.update_or_create(
                name=entry["name"],
                country=entry["country"],
                defaults={
                    "city": entry.get(
                        "city",
                        "",
                    ),
                    "latitude": entry.get(
                        "latitude",
                    ),
                    "longitude": entry.get(
                        "longitude",
                    ),
                    "image_url": entry.get(
                        "image_url",
                        "",
                    ),
                    "is_active": entry.get(
                        "is_active",
                        True,
                    ),
                },
            )

            if was_created:

                created += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created: "
                        f"{entry['name']}, "
                        f"{entry['country']}"
                    )
                )

            else:

                updated += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Updated: "
                        f"{entry['name']}, "
                        f"{entry['country']}"
                    )
                )

        if not dry_run:

            self.stdout.write(
                self.style.SUCCESS(
                    f"Seed complete. "
                    f"{created} created, "
                    f"{updated} updated."
                )
            )