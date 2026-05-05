from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import LoginView, RegistrationView

app_name = "accounts"

urlpatterns = [
    path("register", RegistrationView.as_view(), name="register"),
    path("login", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
]
