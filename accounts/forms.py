from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm

from theme.forms import ThemedFormMixin

from .models import VERIFICATION_CODE_ALPHABET, User


class LoginForm(ThemedFormMixin, AuthenticationForm):
    pass


class RegistrationForm(ThemedFormMixin, BaseUserCreationForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class VerificationForm(ThemedFormMixin, forms.Form):
    code = forms.CharField(
        min_length=6,
        max_length=6,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "autocapitalize": "characters",
                "autocomplete": "one-time-code",
                "placeholder": "XXXXXX",
            }
        ),
    )
    token = forms.CharField(required=False, strip=True, widget=forms.HiddenInput())

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        if not all(c in VERIFICATION_CODE_ALPHABET for c in code):
            raise forms.ValidationError("Enter a valid verification code.")
        return code
