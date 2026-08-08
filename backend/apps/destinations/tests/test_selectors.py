from django.test import TestCase

from apps.destinations.models import Destination
from apps.destinations.selectors import search_destinations


class SearchDestinationsSelectorTests(TestCase):
    """Tests for search_destinations()."""
    
    def test_returns_empty_queryset_for_blank_query(self):
        """
        Blank queries should never return all destinations.
        """

        Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6895,
            longitude=139.6917,
        )
    
        queryset = search_destinations(
            query="",
        )

        self.assertEqual(
            queryset.count(),
            0,
        )
        
    def test_search_by_destination_name(self):
        """
        The selector should match destination names.
        """

        tokyo = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        Destination.objects.create(
            name="Paris",
            country="France",
            city="Paris",
            latitude=48.8566,
            longitude=2.3522,
        )

        queryset = search_destinations(
            query="Tokyo",
        )

        self.assertEqual(
            queryset.count(),
            1,
        )

        self.assertEqual(
            queryset.first(),
            tokyo,
        )
        
    def test_search_by_country(self):
        """
        The selector should match destination countries.
        """

        japan = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        Destination.objects.create(
            name="Paris",
            country="France",
            city="Paris",
            latitude=48.8566,
            longitude=2.3522,
        )

        queryset = search_destinations(
            query="Japan",
        )

        self.assertEqual(
            queryset.count(),
            1,
        )

        self.assertEqual(
            queryset.first(),
            japan,
        )
        
    def test_search_by_city(self):
        """
        The selector should match destination cities.
        """

        tokyo = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        Destination.objects.create(
            name="Osaka",
            country="Japan",
            city="Osaka",
            latitude=34.6937,
            longitude=135.5023,
        )

        queryset = search_destinations(
            query="Tokyo",
        )

        self.assertEqual(
            queryset.count(),
            1,
        )

        self.assertEqual(
            queryset.first(),
            tokyo,
        )
        
    def test_inactive_destinations_are_not_returned(self):
        """
        Inactive destinations should never appear in search results.
        """

        Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            is_active=False,
        )


        queryset = search_destinations(
            query="Tokyo",
        )

        self.assertEqual(
            queryset.count(),
            0,
        )
        
    def test_returns_summary_description_and_tags(self):
        """
        Selector should preserve knowledge fields.
        """

        destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            summary="Capital of Japan",
            description="Modern city with historic temples.",
            tags=["culture", "food"],
        )

        results = search_destinations(
            query="Tokyo",
        )

        self.assertEqual(
            results.count(),
            1,
        )

        result = results.first()

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
        
    def test_search_matches_destination_knowledge(self):
        """
        Searches should match destination knowledge fields.
        """

        Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            summary="Anime capital",
            description="Famous for technology and temples.",
            tags=["anime", "food"],
        )

        results = search_destinations(
            query="anime",
        )

        self.assertEqual(
            results.count(),
            1,
        )

        self.assertEqual(
            results.first().name,
            "Tokyo",
        )
    