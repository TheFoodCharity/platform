from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import ApplyView

app_name = "accounts"

urlpatterns = [
    path("apply", ApplyView.as_view()),
    path("login", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
]
