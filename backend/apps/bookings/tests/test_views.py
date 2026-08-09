from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.bookings.models import Booking, BookingStatus, BookingType
from apps.trips.models import Trip


class BookingViewTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="owner@example.com",
            password="test-password",
        )
        self.other_user = user_model.objects.create_user(
            email="other@example.com",
            password="test-password",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title="Kerala Trip",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
        )
        self.other_trip = Trip.objects.create(
            user=self.other_user,
            title="Other Trip",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
        )
        self.url = reverse(
            "bookings:trip-booking-list-create",
            kwargs={"trip_pk": self.trip.pk},
        )

    def test_authenticated_user_can_create_booking_intent(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {
                "booking_type": BookingType.HOTEL,
                "title": "Kochi Hotel",
                "estimated_cost": "4500.00",
                "notes": "Near the city centre",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        booking = Booking.objects.get()
        self.assertEqual(booking.trip, self.trip)
        self.assertEqual(booking.status, BookingStatus.INTENT_ONLY)

    def test_list_returns_only_current_trip_bookings(self):
        Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.HOTEL,
            title="My Hotel",
        )
        Booking.objects.create(
            trip=self.other_trip,
            booking_type=BookingType.HOTEL,
            title="Other Hotel",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "My Hotel")

    def test_other_user_cannot_access_trip_bookings(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_is_rejected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_status_is_read_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {
                "booking_type": BookingType.FLIGHT,
                "title": "Flight",
                "status": BookingStatus.CONFIRMED,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        booking = Booking.objects.get()
        self.assertEqual(booking.status, BookingStatus.INTENT_ONLY)

    def test_cross_trip_recommendation_is_rejected(self):
        from apps.destinations.models import Destination
        from apps.recommendations.models import Recommendation, RecommendationCategory

        destination = Destination.objects.create(
            name="Munnar",
            country="India",
            city="Munnar",
            latitude="10.0889",
            longitude="77.0595",
        )
        recommendation = Recommendation.objects.create(
            trip=self.other_trip,
            destination=destination,
            category=RecommendationCategory.ATTRACTION,
            score="0.90",
            reason="Other user's recommendation.",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {
                "booking_type": BookingType.ACTIVITY,
                "title": "Munnar Activity",
                "source_recommendation": str(recommendation.pk),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Booking.objects.exists())
