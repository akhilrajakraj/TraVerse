from django.test import TestCase

from ai.tools.destination_search import DestinationSearchResult

from apps.ai_agents.destination_search import search_destination
from apps.destinations.models import Destination

from decimal import Decimal 

class DestinationSearchExecutorTests(TestCase):
    """Tests for the destination search executor."""
    
    def test_returns_empty_list_when_no_destination_matches(self):
        """
        Unknown destinations should return an empty list.
        """

        results = search_destination(
            query="Atlantis",
        )

        self.assertEqual(
            results,
            [],
        )
        
    def test_returns_matching_destination(self):
        """
        Matching destinations should be converted into
        DestinationSearchResult objects.
        """

        Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            summary="Capital of Japan",
            description="Modern city with historic temples.",
            tags=["culture", "food"],
            latitude=35.6762,
            longitude=139.6503,
        )

        results = search_destination(
            query="Tokyo",
        )

        self.assertEqual(
            len(results),
            1,
        )

        result = results[0]

        self.assertIsInstance(
            result,
            DestinationSearchResult,
        )

        self.assertEqual(
            result.name,
            "Tokyo",
        )

        self.assertEqual(
            result.country,
            "Japan",
        )

        self.assertEqual(
            result.city,
            "Tokyo",
        )

        self.assertEqual(
            result.latitude,
            Decimal("35.6762"),
        )

        self.assertEqual(
            result.longitude,
            Decimal("139.6503"),
        )
        
        self.assertEqual(
        result.summary,
        "Capital of Japan",
        )

        self.assertEqual(
        result.description,
        "Modern city with historic temples.",
        )

        self.assertEqual(
        result.tags,
        ["culture", "food"],
        )