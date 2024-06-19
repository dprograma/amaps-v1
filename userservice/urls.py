from django.urls import path

from userservice.views import (
    AboutView,
    ActivationSentView,
    ActivationView,
    DeleteAccountView,
    ForgotPasswordView,
    HomeView,
    LoginView,
    LogoutView,
    PasswordResetView,
    SignupView,
    UpdateUserView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("", AboutView.as_view(), name="about"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("activation-sent/", ActivationSentView.as_view(), name="activation_sent"),
    path("activate/<str:uidb64>/<str:token>/", ActivationView.as_view(), name="activate"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path(
        "reset-password/<str:uidb64>/<str:token>/",
        PasswordResetView.as_view(),
        name="reset_password",
    ),
    path("update-user/", UpdateUserView.as_view(), name="update_user"),
    path("delete-account/", DeleteAccountView.as_view(), name="delete_account"),
]
