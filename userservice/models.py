from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .constants import MAX_LOGIN_ATTEMPTS


class Users(AbstractUser):
    # Add any additional fields you want to include in your User model
    # For example:
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_user_agent = models.TextField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    # Override any methods or add custom methods to the model as needed
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        app_label = "userservice"

    def __str__(self):
        return self.username


class LoginAttemptManager(models.Manager):
    def add_attempt(self, ip_address):
        """Add a login attempt for the given IP address."""
        attempt, created = self.get_or_create(ip_address=ip_address)
        if created:
            attempt.attempts += 1
            attempt.ip_address
            attempt.last_attempt_time = timezone.now()
            attempt.save()
        else:
            attempt.attempts += 1
            attempt.ip_address
            attempt.last_attempt_time = timezone.now()
            attempt.save()

    def get_attempts(self, ip_address):
        """Get the number of login attempts for the given IP address."""
        attempt = self.filter(ip_address=ip_address).first()
        if attempt:
            return attempt.attempts
        return 0

    def reset_attempts(self, ip_address):
        """Reset the login attempts for the given IP address."""
        self.filter(ip_address=ip_address).delete()

    def is_ip_locked(self, ip_address):
        """
        Check if the IP address is locked due to too many login attempts.
        """
        try:
            login_attempt = self.get(ip_address=ip_address)
            if login_attempt and login_attempt.attempts >= MAX_LOGIN_ATTEMPTS:
                time_difference = timezone.now() - login_attempt.last_attempt_time
                return time_difference <= login_attempt.lockout_duration
        except LoginAttempt.DoesNotExist:
            return False


class LoginAttempt(models.Model):
    ip_address = models.CharField(max_length=45, unique=True)
    attempts = models.PositiveIntegerField(default=0)
    last_attempt_time = models.DateTimeField(auto_now=True, null=True, blank=True)
    lockout_duration = models.DurationField(default=timedelta(seconds=900))
    max_login_attempts = models.PositiveIntegerField(default=MAX_LOGIN_ATTEMPTS)

    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='login_attempts', null=True, blank=True)

    def save(self, *args, **kwargs):
        super(LoginAttempt, self).save(*args, **kwargs)

        if self.user and self.attempts >= 3:
            self.user.is_locked = True
            self.user.save()

    class Meta:
        app_label = "userservice"

    objects = LoginAttemptManager()
