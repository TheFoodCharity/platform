from django import forms

from organizations.models import Organization
from theme.forms import ThemedFormMixin

from .models import CollaborationChatMessage, CollaborationSpaceRequest


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
