from django.contrib.auth.forms import BaseUserCreationForm

from .models import User


class RegistrationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]
