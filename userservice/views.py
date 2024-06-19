from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import DeleteView, UpdateView, View

from userservice.forms import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignupForm

from . import constants
from .models import LoginAttempt, Users
from .sendmail import SendMail


class HomeView(View):
    template_name = "userservice/home.html"

    def get(self, request):
        context = {}
        return render(request, self.template_name, context)


class AboutView(View):
    template_name = "userservice/about.html"

    def get(self, request):
        context = {}
        return render(request, self.template_name, context)


class ActivationSentView(View):
    template_name = "userservice/activation_sent.html"

    def get(self, request):
        context = {}
        return render(request, self.template_name, context)


class SignupView(View):
    template_name = "userservice/signup.html"
    form_class = SignupForm
    success_url = "userservice/activation_sent.html"

    def get(self, request):
        form = self.form_class()
        return TemplateResponse(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        tab = request.POST.get("tab", "email")  # Get the value of the selected tab
        if tab == "mobile":
            form.fields["email"].required = False  # Make the email field optional for mobile sign-up
        else:
            form.fields["phone_number"].required = False  # Make the phone number field optional for email sign-up
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            email = form.cleaned_data["email"] or None
            phone = form.cleaned_data["phone_number"] or None

            user = Users.objects.create_user(username=username, password=password, email=email, phone_number=phone)
            user.is_active = False
            user.save()

            # Send email confirmation
            current_site = Site.objects.first()
            mail_subject = "Activate your account"
            message = render_to_string(
                "userservice/activation_email.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            email = SendMail(mail_subject, message, to_email)
            messages.info(request, "Your account has been created. An activation email has been sent to you.")

            return render(request, self.success_url)
        messages.error(request, "Please fix the error(s) in your form submission and continue.")
        return render(request, self.template_name, {"form": form})


class ActivationView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Users.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Users.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(
                request,
                "Your account has been activated successfully. You can now log in.",
            )
        else:
            messages.error(request, "Invalid activation link.")

        return redirect("login")


class LoginView(View):
    template_name = "userservice/signin.html"
    form_class = LoginForm
    success_url = reverse_lazy("home")
    max_login_attempts = constants.MAX_LOGIN_ATTEMPTS
    lockout_duration = 900  # 15 minutes in seconds

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        tab = request.POST.get("tab", "email")  # Get the value of the selected tab
        if tab == "mobile":
            form.fields["email"].required = False  # Make the email field optional for mobile sign-up
        else:
            form.fields["phone_number"].required = False  # Make the phone number field optional for email sign-up

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]

            # Check if the IP is locked
            ip_address = request.META.get("REMOTE_ADDR")
            if LoginAttempt.objects.is_ip_locked(ip_address):
                messages.error(
                    request,
                    "Your IP address is locked. Please try again after 15 minutes or contact support.",
                )
                return redirect("login")

            user = authenticate(request, email=email, password=password)

            if user is not None:
                # Check if the user account is locked
                if user.is_locked:
                    messages.error(
                        request,
                        "Your account is locked. Please contact support to resolve your account.",
                    )
                    return redirect("login")

                # Login successful, reset login attempts
                LoginAttempt.objects.reset_attempts(ip_address)

                login(request, user)
                user_agent = request.META.get("HTTP_USER_AGENT")
                # Check if the user logged in from a new device
                if user.last_login_ip != ip_address or user_agent != user.last_login_user_agent:
                    # Send email notification to the user
                    message = render_to_string(
                        "userservice/send_new_device_notification.html",
                        {
                            "user": user,
                            "ip_address": ip_address,
                            "device": user_agent,
                            "datetime": timezone.now(),
                            "site_name": Site.objects.first(),
                        },
                    )
                    mail_subject = "New Device Login Notification"
                    email = SendMail(mail_subject, message, email)
                    email.send()

                return redirect("home")
            else:
                # Login failed, increase login attempts
                LoginAttempt.objects.add_attempt(ip_address)
                remaining_attempts = self.max_login_attempts - LoginAttempt.objects.get_attempts(ip_address)

                if remaining_attempts > 0:
                    messages.error(
                        request,
                        f"Invalid login credentials. You have {remaining_attempts} attempts remaining.",
                    )
                else:
                    messages.error(
                        request,
                        "Invalid login credentials. Your IP address has been locked for 15 minutes.",
                    )

        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("home")


class ForgotPasswordView(View):
    template_name = "userservice/forgot_password.html"
    form_class = ForgotPasswordForm
    success_url = reverse_lazy("password_reset_done")

    def get(self, request):
        form = ForgotPasswordForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            user = Users.objects.filter(email=email).first()

            if user is not None:
                current_site = get_current_site(request)
                mail_subject = "Reset your password"
                message = render_to_string(
                    "username/password_reset_email.html",
                    {
                        "user": user,
                        "domain": current_site.domain,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "token": default_token_generator.make_token(user),
                    },
                )
                to_email = email
                email = SendMail(mail_subject, message, to_email)
                email.send()

        return render(request, self.template_name, {"form": form})


class PasswordResetView(View):
    template_name = "userservice/password_reset.html"
    form_class = ResetPasswordForm
    success_url = reverse_lazy("password_reset_complete")

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Users.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Users.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = ResetPasswordForm(user)
            context = {"form": form, "uidb64": uidb64, "token": token}
            return render(request, self.template_name, context)
        else:
            messages.error(request, "Invalid password reset link.")
            return redirect("forgot_password")

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Users.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Users.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = ResetPasswordForm(user, request.POST)

            if form.is_valid():
                form.save()
                messages.success(
                    request,
                    "Your password has been reset successfully. You can now log in.",
                )
                return redirect("login")
            else:
                messages.error(request, "Please correct the errors below.")
                context = {"form": form, "uidb64": uidb64, "token": token}
                return render(request, self.template_name, context)
        else:
            messages.error(request, "Invalid password reset link.")
            return redirect("forgot_password")


class UpdateUserView(LoginRequiredMixin, UpdateView):
    model = Users
    template_name = "userservice/update_user.html"
    fields = ["username", "email"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.request.user


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = Users
    template_name = "userservice/delete_account.html"
    success_url = reverse_lazy("login")
    slug_field = "username"
    slug_url_kwarg = "username"
