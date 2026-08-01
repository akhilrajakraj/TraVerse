"""
Management command tests for the Destinations application.
"""

import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.destinations.models import Destination


class SeedDestinationsCommandTests(TestCase):
    """
    Test suite for the seed_destinations management command.
    """

    @property
    def fixture_data(self):
        return [
            {
                "name": "Tokyo",
                "country": "Japan",
                "city": "Tokyo",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "image_url": "",
                "is_active": True,
            },
            {
                "name": "Paris",
                "country": "France",
                "city": "Paris",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "image_url": "",
                "is_active": True,
            },
        ]

    @patch("apps.destinations.management.commands.seed_destinations.FIXTURE_PATH")
    def test_seed_creates_destinations(self, mock_path):
        """
        Command should create destinations from the fixture.
        """

        temp_file = Path("/tmp/test_destinations.json")
        temp_file.write_text(
            json.dumps(self.fixture_data),
            encoding="utf-8",
        )

        mock_path.read_text.return_value = temp_file.read_text()

        call_command(
            "seed_destinations",
        )

        self.assertEqual(
            Destination.objects.count(),
            2,
        )

    @patch("apps.destinations.management.commands.seed_destinations.FIXTURE_PATH")
    def test_seed_is_idempotent(self, mock_path):
        """
        Running the command twice should not create duplicates.
        """

        temp_file = Path("/tmp/test_destinations.json")
        temp_file.write_text(
            json.dumps(self.fixture_data),
            encoding="utf-8",
        )

        mock_path.read_text.return_value = temp_file.read_text()

        call_command(
            "seed_destinations",
        )

        call_command(
            "seed_destinations",
        )

        self.assertEqual(
            Destination.objects.count(),
            2,
        )

    @patch("apps.destinations.management.commands.seed_destinations.FIXTURE_PATH")
    def test_dry_run_does_not_modify_database(self, mock_path):
        """
        Dry-run should not create destinations.
        """

        temp_file = Path("/tmp/test_destinations.json")
        temp_file.write_text(
            json.dumps(self.fixture_data),
            encoding="utf-8",
        )

        mock_path.read_text.return_value = temp_file.read_text()

        call_command(
            "seed_destinations",
            "--dry-run",
        )

        self.assertEqual(
            Destination.objects.count(),
            0,
        )