import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'userservice.settings')
django.setup()

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from userservice.forms import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignupForm

User = get_user_model()


@pytest.mark.django_db
class TestSignupForm(TestCase):
    def test_signup_form(self):
        form = SignupForm(
            data={
                "username": "testuser",
                "phone_number": "1234567890",
                "email": "test@example.com",
                "password1": "Pa$$word123",
                "password2": "Pa$$word123",
            }
        )
        assert form.is_valid()

        user = form.save()
        assert user.username == "testuser"
        assert user.phone_number == "1234567890"
        assert user.email == "test@example.com"


@pytest.mark.django_db
class TestLoginForm(TestCase):
    def test_login_form(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="Pa$$word123")
        form = LoginForm(
            data={
                "email": "test@example.com",
                "password1": "Pa$$word123",
                "phone_number": "1234567890",
            }
        )
        assert form.is_valid()

        assert form.cleaned_data["email"] == "test@example.com"
        assert form.cleaned_data["phone_number"] == "1234567890"


@pytest.mark.django_db
class TestForgotPasswordForm(TestCase):
    def test_forgot_password_form(self):
        form = ForgotPasswordForm(
            data={
                "email": "test@example.com",
            }
        )
        assert form.is_valid()

        assert form.cleaned_data["email"] == "test@example.com"


@pytest.mark.django_db
class TestResetPasswordForm(TestCase):
    def test_reset_password_form(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="Password123")
        form = ResetPasswordForm(
            user=user,
            data={
                "new_password1": "newPa$$word123",
                "new_password2": "newPa$$word123",
            },
        )
        assert form.is_valid()

        assert form.cleaned_data["new_password1"] == "newPa$$word123"
        assert form.cleaned_data["new_password2"] == "newPa$$word123"
