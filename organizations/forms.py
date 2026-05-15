from crispy_forms.layout import Fieldset, Layout, Row
from django.forms import fields, forms
from django.forms.models import ModelForm

from organizations.models import Organization
from theme.forms import ThemedFormMixin


class ApplicationCreateForm(ThemedFormMixin, ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "organization_type"]


class ApplicationBasicDetailsForm(ThemedFormMixin, ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "organization_type", "legal_status", "description"]


class ApplicationLocationForm(ThemedFormMixin, ModelForm):
    class Meta:
        model = Organization
        fields = [
            "address_line_1",
            "address_line_2",
            "municipality",
            "region",
            "postal_code",
            "service_area",
            "latitude",
            "longitude",
        ]


class ApplicationContactForm(ThemedFormMixin, ModelForm):
    class Meta:
        model = Organization
        fields = ["email", "phone", "website"]


class ApplicationOperationsForm(ThemedFormMixin, ModelForm):
    class Meta:
        model = Organization
        fields = ["interest_areas", "contact_via_email", "contact_via_phone"]


class ApplicationSubmitForm(ThemedFormMixin, forms.Form):
    acknowledged = fields.BooleanField(
        required=False,
        label="I understand and agree to the above",
    )

    def __init__(self, *args, organization_status=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization_status == Organization.Status.DRAFT:
            self.fields["acknowledged"].required = True


class ProfileForm(ThemedFormMixin, ModelForm):
    def __init__(self, *args, editable=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not editable:
            for field in self.fields.values():
                field.disabled = True

    layout = Layout(
        "name",
        "description",
        Row("organization_type", "legal_status"),
        "interest_areas",
        Fieldset(
            "Location",
            Row("address_line_1", "address_line_2"),
            Row("municipality", "region", "postal_code"),
            "service_area",
        ),
        Fieldset(
            "Contact Details",
            Row("email", "contact_via_email", css_class="items-center"),
            Row("phone", "contact_via_phone", css_class="items-center"),
            "website",
        ),
    )

    class Meta:
        model = Organization
        fields = [
            "name",
            "organization_type",
            "legal_status",
            "description",
            "interest_areas",
            "address_line_1",
            "address_line_2",
            "municipality",
            "region",
            "postal_code",
            "service_area",
            "email",
            "phone",
            "website",
            "contact_via_phone",
            "contact_via_email",
        ]
