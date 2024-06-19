import os
from datetime import timedelta

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'userservice.settings')
django.setup()

import pytest
from django.test import TestCase
from django.utils import timezone

from userservice.models import LoginAttempt, Users


@pytest.mark.django_db
class TestUsersModel(TestCase):
    def test_users_model(self):
        # Create a sample user
        user = Users.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            address="Test Address",
            phone_number="1234567890",
        )

        # Test the fields and methods of the user model
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpassword"))
        self.assertEqual(user.address, "Test Address")
        self.assertEqual(user.phone_number, "1234567890")
        self.assertEqual(str(user), "testuser")

        # Test the UserManager's create_superuser method
        admin_user = Users.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword",
            address="Admin Address",
            phone_number="0987654321",
        )

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.username, "adminuser")
        self.assertEqual(admin_user.email, "admin@example.com")
        self.assertTrue(admin_user.check_password("adminpassword"))
        self.assertEqual(admin_user.address, "Admin Address")
        self.assertEqual(admin_user.phone_number, "0987654321")
        self.assertEqual(str(admin_user), "adminuser")


@pytest.mark.django_db
class TestLoginAttemptManager(TestCase):
    def test_add_attempt(self):
        ip_address = "127.0.0.1"

        # Test adding a new attempt
        LoginAttempt.objects.add_attempt(ip_address)
        self.assertEqual(LoginAttempt.objects.get_attempts(ip_address), 1)

        # Test adding an existing attempt
        LoginAttempt.objects.add_attempt(ip_address)
        self.assertEqual(LoginAttempt.objects.get_attempts(ip_address), 2)

    def test_get_attempts(self):
        ip_address = "127.0.0.2"

        # Test getting attempts for a non-existing IP address
        attempts = LoginAttempt.objects.get_attempts(ip_address)
        self.assertEqual(attempts, 0)

        # Test getting attempts for an existing IP address
        LoginAttempt.objects.add_attempt(ip_address)
        attempts = LoginAttempt.objects.get_attempts(ip_address)
        self.assertEqual(attempts, 1)

    def test_reset_attempts(self):
        ip_address = "127.0.0.3"
        # manager = LoginAttemptManager()

        # Test resetting attempts for a non-existing IP address
        LoginAttempt.objects.reset_attempts(ip_address)
        self.assertFalse(LoginAttempt.objects.filter(ip_address=ip_address).exists())

        # Test resetting attempts for an existing IP address
        LoginAttempt.objects.add_attempt(ip_address)
        LoginAttempt.objects.reset_attempts(ip_address)
        self.assertFalse(LoginAttempt.objects.filter(ip_address=ip_address).exists())

    def test_is_ip_locked(self):
        ip_address = "127.0.0.4"

        # Test IP address is not locked
        self.assertFalse(LoginAttempt.objects.is_ip_locked(ip_address))

        # Test IP address is locked
        attempt = LoginAttempt.objects.create(ip_address=ip_address, attempts=5)
        self.assertTrue(LoginAttempt.objects.is_ip_locked(ip_address))


@pytest.mark.django_db
class TestLoginAttempt(TestCase):
    def test_save(self):
        user = Users.objects.create(username="testuser")
        attempt = LoginAttempt.objects.create(ip_address="127.0.0.10", attempts=3, user=user)

        # Test that the user is locked after saving the attempt
        user.refresh_from_db()
        self.assertTrue(user.is_locked)

        # Test that the user is not locked when attempts are less than 3
        attempt.attempts = 2
        attempt.save()
        user.refresh_from_db()
        self.assertFalse(user.login_attempts.is_ip_locked('127.0.0.10'))

    def test_lockout_duration(self):
        user = Users.objects.create(username="testuser1")
        # attempt = LoginAttempt.objects.create(ip_address="127.0.0.11", attempts=3, user=user)

        # Create an attempt with a past last_attempt_time
        past_time = timezone.now() - timedelta(seconds=900)
        LoginAttempt.objects.create(ip_address='127.0.0.11', attempts=5, last_attempt_time=past_time, user=user)
        user.refresh_from_db()
        # Test that the IP address is not locked after the lockout duration
        # self.assertFalse(user.login_attempts.is_ip_locked('127.0.0.11'))
