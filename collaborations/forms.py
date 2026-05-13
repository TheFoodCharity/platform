from pathlib import Path
from zipfile import BadZipFile, ZipFile

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from donations.models import Donation, FoodRequest
from organizations.models import Organization
from storage.models import StorageLocation
from theme.forms import ThemedFormMixin

from .models import (
    CollaborationChatMessage,
    CollaborationFile,
    CollaborationLinkedObject,
    CollaborationSpaceRequest,
)

MAX_COLLABORATION_FILE_SIZE = settings.COLLABORATION_FILE_UPLOAD_MAX_SIZE
ALLOWED_COLLABORATION_FILE_TYPES = {
    ".pdf": {"application/pdf"},
    ".ppt": {
        "application/vnd.ms-powerpoint",
        "application/mspowerpoint",
        "application/x-mspowerpoint",
    },
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}


def _uploaded_file_matches_extension(uploaded_file, extension):
    uploaded_file.seek(0)
    try:
        match extension:
            case ".pdf":
                return uploaded_file.read(5) == b"%PDF-"
            case ".png":
                return uploaded_file.read(8) == b"\x89PNG\r\n\x1a\n"
            case ".jpg" | ".jpeg":
                return uploaded_file.read(3) == b"\xff\xd8\xff"
            case ".ppt":
                return uploaded_file.read(8) == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
            case ".pptx":
                return _uploaded_file_is_powerpoint_zip(uploaded_file)
            case _:
                return False
    finally:
        uploaded_file.seek(0)


def _uploaded_file_is_powerpoint_zip(uploaded_file):
    try:
        with ZipFile(uploaded_file) as archive:
            names = set(archive.namelist())
    except BadZipFile:
        return False
    return "[Content_Types].xml" in names and any(name.startswith("ppt/") for name in names)


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


class CollaborationFileUploadForm(ThemedFormMixin, forms.ModelForm):
    class Meta:
        model = CollaborationFile
        fields = ["file"]
        labels = {
            "file": "File",
        }
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"}),
        }

    def __init__(self, *args, space=None, uploaded_by=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.space = space
        self.uploaded_by = uploaded_by

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        original_filename = Path(uploaded_file.name).name
        extension = Path(original_filename).suffix.lower()
        content_type = getattr(uploaded_file, "content_type", "")

        if not original_filename:
            raise forms.ValidationError("Upload a valid file.")

        if len(original_filename) > CollaborationFile._meta.get_field("original_filename").max_length:
            raise forms.ValidationError("The file name is too long.")

        if extension not in ALLOWED_COLLABORATION_FILE_TYPES:
            raise forms.ValidationError("Upload a PDF, PowerPoint, JPG, or PNG file.")

        if content_type not in ALLOWED_COLLABORATION_FILE_TYPES[extension]:
            raise forms.ValidationError("The uploaded file type does not match the file extension.")

        if not _uploaded_file_matches_extension(uploaded_file, extension):
            raise forms.ValidationError("The uploaded file contents do not match the file extension.")

        if uploaded_file.size > MAX_COLLABORATION_FILE_SIZE:
            raise forms.ValidationError("Upload a file smaller than 50 MB.")

        return uploaded_file

    def save(self, commit=True):
        if self.uploaded_by is None:
            raise ValueError("CollaborationFileUploadForm requires uploaded_by before saving.")

        collaboration_file = super().save(commit=False)
        uploaded_file = self.cleaned_data["file"]
        collaboration_file.space = self.space
        collaboration_file.original_filename = Path(uploaded_file.name).name
        collaboration_file.content_type = uploaded_file.content_type
        collaboration_file.size = uploaded_file.size
        collaboration_file.uploaded_by = self.uploaded_by

        if commit:
            collaboration_file.save()
        return collaboration_file


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
