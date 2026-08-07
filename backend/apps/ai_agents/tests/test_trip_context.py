from datetime import date
from decimal import Decimal

from django.test import TestCase

from ai.context.trip_context import TripContextBuilder

from apps.accounts.models import User
from apps.destinations.models import Destination
from apps.itinerary.models import ItineraryDay
from apps.trips.models import Trip, PackingCategory, PackingItem


class TripContextBuilderTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.destination = Destination.objects.create(
            name="Tokyo Tower",
            city="Tokyo",
            country="Japan",
            latitude=Decimal("35.6586"),
            longitude=Decimal("139.7454"),
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 15),
        )

        self.trip.destinations.add(
            self.destination,
        )

    def test_trip_information(self):

        context = TripContextBuilder.build(
            trip=self.trip,
        )

        self.assertIn(
            "=== TRIP ===",
            context,
        )

        self.assertIn(
            "Japan Trip",
            context,
        )

    def test_destination_section(self):

        context = TripContextBuilder.build(
            trip=self.trip,
        )

        self.assertIn(
            "=== DESTINATIONS ===",
            context,
        )

        self.assertIn(
            "Tokyo, Japan",
            context,
        )

    def test_weather_section(self):

        ItineraryDay.objects.create(
            trip=self.trip,
            date=self.trip.start_date,
            day_number=1,
            weather_condition="Sunny",
            weather_high_f=84,
            weather_low_f=72,
            weather_precipitation_chance=10,
        )

        context = TripContextBuilder.build(
            trip=self.trip,
        )

        self.assertIn(
            "=== WEATHER ===",
            context,
        )

        self.assertIn(
            "Sunny",
            context,
        )

        self.assertIn(
            "84°F",
            context,
        )

        self.assertIn(
            "72°F",
            context,
        )

        self.assertIn(
            "10% precipitation",
            context,
        )

    def test_itinerary_section(self):

        ItineraryDay.objects.create(
            trip=self.trip,
            date=self.trip.start_date,
            day_number=1,
            summary="Explore Tokyo",
        )

        context = TripContextBuilder.build(
            trip=self.trip,
        )

        self.assertIn(
            "=== ITINERARY ===",
            context,
        )

        self.assertIn(
            "Day 1",
            context,
        )

    def test_packing_section(self):

        PackingItem.objects.create(
            trip=self.trip,
            category=PackingCategory.CLOTHING,
            item="Jacket",
            quantity=1,
            reason="Cold evenings",
        )

        context = TripContextBuilder.build(
            trip=self.trip,
        )

        self.assertIn(
            "=== PACKING ===",
            context,
        )

        self.assertIn(
            "Jacket",
            context,
        )