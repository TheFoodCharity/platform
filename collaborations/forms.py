from django import forms
from django.contrib.contenttypes.models import ContentType

from donations.models import Donation, FoodRequest
from organizations.models import Organization
from storage.models import StorageLocation
from theme.forms import ThemedFormMixin

from .models import (
    CollaborationChatMessage,
    CollaborationLinkedObject,
    CollaborationSpaceRequest,
)


class CollaborationSpaceRequestForm(ThemedFormMixin, forms.ModelForm):
    class Meta:
        model = CollaborationSpaceRequest
        fields = [
            "title",
            "purpose",
            "topic_category",
            "region",
            "municipality",
            "suggested_participants",
            "visibility_preference",
            "reason_for_request",
            "requested_by_org",
        ]
        widgets = {
            "purpose": forms.Textarea(attrs={"rows": 4}),
            "suggested_participants": forms.Textarea(attrs={"rows": 3}),
            "reason_for_request": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        organizations = Organization.objects.none()
        if user and user.is_authenticated:
            organizations = user.organizations.all()
        self.fields["requested_by_org"].queryset = organizations
        self.fields["requested_by_org"].required = False


class CollaborationChatMessageForm(forms.ModelForm):
    class Meta:
        model = CollaborationChatMessage
        fields = ["body"]
        labels = {
            "body": "Message",
        }
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered min-h-28 w-full",
                    "rows": 3,
                    "placeholder": "Write a message to this collaboration",
                }
            ),
        }


class CollaborationLinkedRecordForm(ThemedFormMixin, forms.Form):
    record = forms.ChoiceField(
        label="Record",
        choices=[],
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    label = forms.CharField(
        label="Display label",
        required=False,
        widget=forms.TextInput(attrs={"class": "input input-bordered w-full"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
    )

    def __init__(self, *args, space=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.space = space
        self._record_map = {}
        self.fields["record"].choices = self._record_choices()

    def _record_choices(self):
        choices = [("", "Select a record")]
        choices.extend(self._donation_choices())
        choices.extend(self._storage_choices())
        choices.extend(self._food_request_choices())
        return choices

    def _donation_choices(self):
        choices = []
        for donation in Donation.objects.order_by("-created_at")[:100]:
            key = f"donation:{donation.pk}"
            label = f"Donation #{donation.pk} - {donation.food_type_display} ({donation.get_status_display()})"
            self._record_map[key] = (donation, label)
            choices.append((key, label))
        return choices

    def _storage_choices(self):
        choices = []
        for location in StorageLocation.objects.filter(is_active=True).order_by("name")[:100]:
            key = f"storage:{location.pk}"
            label = f"Storage #{location.pk} - {location.name} ({location.get_capacity_status_display()})"
            self._record_map[key] = (location, label)
            choices.append((key, label))
        return choices

    def _food_request_choices(self):
        choices = []
        food_requests = FoodRequest.objects.select_related("donation").order_by("-created_at")[:100]
        for food_request in food_requests:
            key = f"food_request:{food_request.pk}"
            label = (
                f"Food request #{food_request.pk} - {food_request.receiver_name} ({food_request.get_status_display()})"
            )
            self._record_map[key] = (food_request, label)
            choices.append((key, label))
        return choices

    def clean_record(self):
        record_key = self.cleaned_data["record"]
        if record_key not in self._record_map:
            raise forms.ValidationError("Select a valid record.")

        record, _ = self._record_map[record_key]
        if (
            self.space
            and CollaborationLinkedObject.objects.filter(
                space=self.space,
                content_type=ContentType.objects.get_for_model(record),
                object_id=str(record.pk),
            ).exists()
        ):
            raise forms.ValidationError("This record is already linked to the collaboration.")
        return record_key

    def save(self, *, created_by):
        record, default_label = self._record_map[self.cleaned_data["record"]]
        return CollaborationLinkedObject.objects.create(
            space=self.space,
            content_type=ContentType.objects.get_for_model(record),
            object_id=str(record.pk),
            label=self.cleaned_data["label"] or default_label,
            notes=self.cleaned_data["notes"],
            created_by=created_by,
        )
