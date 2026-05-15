from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    ProfileView,
    RegistrationView,
    ResendVerificationView,
    UpdatePasswordView,
    VerifyView,
)

app_name = "accounts"

urlpatterns = [
    path("register", RegistrationView.as_view(), name="register"),
    path("login", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("verify", VerifyView.as_view(), name="verify"),
    path("verify/resend", ResendVerificationView.as_view(), name="verify_resend"),
    path("password-reset", PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/<uidb64>/<token>", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("profile/password", UpdatePasswordView.as_view(), name="update_password"),
]
