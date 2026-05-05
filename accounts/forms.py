from django.contrib.auth.forms import BaseUserCreationForm
from django.forms import ModelForm

from .models import Organization, User


class UserRegistrationForm(BaseUserCreationForm):
    class Meta:
        model = User
        # TODO(alex): see if we can remove the username field
        fields = ["username", "email", "first_name", "last_name"]


class OrganizationRegistrationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["name"]
