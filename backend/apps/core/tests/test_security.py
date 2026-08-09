from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from apps.core.models import AuditLogEntry
from apps.core.rate_limiting import increment_rate_limit, is_rate_limited
from apps.core.services import log_audit_event


User = get_user_model()


class RateLimitingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_not_limited_below_max(self):
        for _ in range(4):
            increment_rate_limit(key="test:rl", window_seconds=60)
        self.assertFalse(is_rate_limited(key="test:rl", max_requests=5))

    def test_limited_at_max(self):
        for _ in range(5):
            increment_rate_limit(key="test:rl2", window_seconds=60)
        self.assertTrue(is_rate_limited(key="test:rl2", max_requests=5))


class AuditLogTests(TestCase):
    def test_log_audit_event_creates_entry(self):
        user = User.objects.create_user(
            email="audit@example.com",
            password="pass1234",
        )
        entry = log_audit_event(
            user=user,
            action="login",
            ip_address="127.0.0.1",
        )
        self.assertEqual(entry.action, "login")
        self.assertEqual(entry.ip_address, "127.0.0.1")
        self.assertEqual(AuditLogEntry.objects.count(), 1)

    def test_entry_survives_user_deletion(self):
        user = User.objects.create_user(
            email="audit2@example.com",
            password="pass1234",
        )
        entry = log_audit_event(user=user, action="login")
        user.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.user)
