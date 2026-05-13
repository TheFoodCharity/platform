from django.urls import path

from .views import LoginView, LogoutView, RegistrationView, ResendVerificationView, VerifyView

app_name = "accounts"

urlpatterns = [
    path("register", RegistrationView.as_view(), name="register"),
    path("login", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("verify", VerifyView.as_view(), name="verify"),
    path("verify/resend", ResendVerificationView.as_view(), name="verify_resend"),
]
