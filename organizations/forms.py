from crispy_forms.layout import Fieldset, Layout, Row
from django.db import models
from django.forms import BooleanField, CharField, ChoiceField, ModelChoiceField, RadioSelect, fields, forms
from django.forms.models import ModelForm

from permissions import Scope
from permissions.models import MembershipPermissionOverride, PermissionGroup
from permissions.registry import registered_permissions
from theme.forms import ThemedFormMixin

from .models import Invitation, Organization


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


class OverrideEffect(models.TextChoices):
    ALLOW = "allow", "Allow"
    DENY = "deny", "Deny"

    @classmethod
    def from_model(cls, effect: int) -> "OverrideEffect":
        return cls.ALLOW if effect == MembershipPermissionOverride.Effect.ALLOW else cls.DENY

    def to_model(self) -> int:
        return (
            MembershipPermissionOverride.Effect.ALLOW
            if self == OverrideEffect.ALLOW
            else MembershipPermissionOverride.Effect.DENY
        )


class MemberPermissionsForm(ThemedFormMixin, forms.Form):
    role = ModelChoiceField(
        queryset=PermissionGroup.objects.filter(scope=Scope.USER),
        required=False,
        label="Role",
    )

    new_permission = CharField(required=False)
    new_effect = ChoiceField(choices=OverrideEffect.choices, required=False, widget=RadioSelect)

    def __init__(self, *args, membership, **kwargs):
        super().__init__(*args, **kwargs)
        self.membership = membership
        self.fields["role"].initial = membership.role_id

        existing = list(membership.permission_overrides.select_related("permission").order_by("permission__code"))
        self.existing_rows = []
        descriptions = registered_permissions()
        existing_codes = set()
        for override in existing:
            code = override.permission.code
            existing_codes.add(code)
            effect_name = f"existing__{code}__effect"
            remove_name = f"existing__{code}__remove"
            self.fields[effect_name] = ChoiceField(
                choices=OverrideEffect.choices,
                initial=OverrideEffect.from_model(override.effect),
                widget=RadioSelect,
                required=False,
            )
            self.fields[remove_name] = BooleanField(required=False)
            self.existing_rows.append(
                {
                    "code": code,
                    "description": descriptions.get(code, {}).get("description", ""),
                    "effect_field": self[effect_name],
                    "remove_field": self[remove_name],
                }
            )

        self.available_permissions = [
            {"code": code, "description": entry["description"]}
            for code, entry in sorted(descriptions.items())
            if code not in existing_codes
        ]
        self._available_codes = {p["code"] for p in self.available_permissions}

    def clean(self):
        data = super().clean()
        new_perm = (data.get("new_permission") or "").strip()
        new_effect = data.get("new_effect") or ""
        if new_perm and not new_effect:
            self.add_error("new_effect", "Choose Allow or Deny for the new override.")
        if new_perm and new_perm not in self._available_codes:
            self.add_error("new_permission", "Unknown or already-overridden permission.")
        return data

    def actions(self):
        """Yield (action, code, effect) tuples for the service."""
        cleaned = self.cleaned_data
        for row in self.existing_rows:
            code = row["code"]
            if cleaned.get(f"existing__{code}__remove"):
                yield "remove", code, None
                continue
            raw = cleaned.get(f"existing__{code}__effect") or OverrideEffect.ALLOW
            yield "update", code, OverrideEffect(raw).to_model()

        new_perm = (cleaned.get("new_permission") or "").strip()
        new_effect_str = cleaned.get("new_effect") or ""
        if new_perm and new_effect_str:
            yield "create", new_perm, OverrideEffect(new_effect_str).to_model()


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


class InvitationSendForm(ThemedFormMixin, ModelForm):
    class Meta:
        model = Invitation
        fields = ["email"]

    def __init__(self, *args, invited_by, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.invited_by = invited_by
        self.organization = organization

    def save(self, commit=True):
        self.instance.organization = self.organization
        self.instance.invited_by = self.invited_by
        return super().save(commit)
