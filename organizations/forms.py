from django.forms import fields, forms
from django.forms.models import ModelForm

from organizations.models import Organization


class ApplicationCreateForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "organization_type"]


class ApplicationBasicDetailsForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "organization_type", "legal_status", "description"]


class ApplicationLocationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["municipality", "region", "service_area"]


class ApplicationContactForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["email", "phone", "website"]


class ApplicationOperationsForm(ModelForm):
    class Meta:
        model = Organization
        fields = ["interest_areas", "contact_via_email", "contact_via_phone"]


class ApplicationSubmitForm(forms.Form):
    acknowledged = fields.BooleanField(required=False)

    def __init__(self, *args, organization_status=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization_status == Organization.Status.DRAFT:
            self.fields["acknowledged"].required = True
