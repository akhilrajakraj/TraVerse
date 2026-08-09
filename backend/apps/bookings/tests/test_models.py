from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.bookings.models import Booking, BookingStatus, BookingType
from apps.destinations.models import Destination
from apps.recommendations.models import (
    Recommendation,
    RecommendationCategory,
)
from apps.trips.models import Trip


class BookingModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com",
            password="test-password",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title="Kerala Trip",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
        )

    def test_defaults_to_intent_only(self):
        booking = Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.HOTEL,
            title="Hotel stay",
        )
        self.assertEqual(booking.status, BookingStatus.INTENT_ONLY)

    def test_uses_uuid_primary_key(self):
        booking = Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.FLIGHT,
            title="Flight",
        )
        self.assertIsNotNone(booking.id)

    def test_trip_deletion_cascades(self):
        Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.ACTIVITY,
            title="Museum",
        )
        self.trip.delete()
        self.assertFalse(Booking.objects.exists())

    def test_recommendation_deletion_sets_source_to_null(self):
        destination = Destination.objects.create(
            name="Kochi",
            country="India",
            city="Kochi",
            latitude="9.9312",
            longitude="76.2673",
        )
        recommendation = Recommendation.objects.create(
            trip=self.trip,
            destination=destination,
            category=RecommendationCategory.ATTRACTION,
            score="0.90",
            reason="Good fit for the trip.",
        )
        booking = Booking.objects.create(
            trip=self.trip,
            source_recommendation=recommendation,
            booking_type=BookingType.ACTIVITY,
            title="Kochi attraction",
        )
        recommendation.delete()
        booking.refresh_from_db()
        self.assertIsNone(booking.source_recommendation)

    def test_orders_newest_first(self):
        first = Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.HOTEL,
            title="First",
        )
        second = Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.FLIGHT,
            title="Second",
        )
        self.assertEqual(list(Booking.objects.all()), [second, first])
