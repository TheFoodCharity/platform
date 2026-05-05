from django.contrib.auth.forms import BaseUserCreationForm
from django.forms import ModelForm

from .models import Organization, User


class UserRegistrationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class OrganizationRegistrationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "email", "phone", "website"]
