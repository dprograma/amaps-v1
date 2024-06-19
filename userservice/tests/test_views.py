import base64
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'userservice.settings')
django.setup()

from unittest import TestCase, mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestSignupView(TestCase):
    def setUp(self):
        self.client = Client()

    @mock.patch("userservice.views.SendMail.send")
    def test_signup_view(self, mock_send):
        signup_data = {
            "email": "test@example.com",
            "password1": "Testpa$$word",
            "password2": "Testpa$$word",
            "phone_number": "1234567890",
            "username": "testuser",
        }
        # Mock reverse_lazy to return the desired URL
        response = self.client.post(reverse("signup"), data=signup_data)

        self.assertEqual(response.status_code, 200)
        # self.assertRedirects(response, "/activation_sent/")

        # Check that the user is created but not active yet
        self.assertTrue(User.objects.filter(email=signup_data["email"]).exists())
        user = User.objects.get(email=signup_data["email"])
        self.assertFalse(user.is_active)

        # Check if activation email is attempted to be sent (no actual email sending)
        mock_send.assert_called_once()


@pytest.mark.django_db
class TestActivationView(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="Testpa$$word")
        self.activation_url = reverse("activate", args=[self.user.pk, "token"])

    def get_uidb64(self):
        # Encode the user's primary key to generate the uidb64
        uidb64 = base64.urlsafe_b64encode(str(self.user.pk).encode()).decode()
        return uidb64

    def test_activation_view(self):
        response = self.client.get(self.activation_url, uidb64=self.get_uidb64(), token="token")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

        # Check that the user is activated
        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.is_active)


@pytest.mark.django_db
class TestLoginView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="Testpa$$word", email="test@example.com")
        self.ip_address = "127.0.0.1"

    @mock.patch("userservice.views.SendMail.send")
    @mock.patch("userservice.models.LoginAttemptManager.is_ip_locked", return_value=True)
    def test_login_view_ip_locked(self, mock_is_ip_locked, mock_send):
        data = {
            "email": self.user.email,
            "password1": "Testpa$$word",
        }

        response = self.client.post(reverse("login"), data=data, REMOTE_ADDR=self.ip_address)

        self.assertEqual(response.status_code, 302)

    @mock.patch("userservice.views.SendMail.send")
    @mock.patch("userservice.models.LoginAttemptManager.is_ip_locked", return_value=False)
    def test_login_view(self, mock_is_ip_locked, mock_send):
        data = {
            "email": self.user.email,
            "password1": "Testpa$$word",
        }

        response = self.client.post(reverse("login"), data=data, REMOTE_ADDR=self.ip_address)

        self.assertEqual(response.status_code, 302)
