from django import forms

from organizations.models import Organization

from .models import ForumPost, ForumSpaceRequest, approved_member_organizations


class ForumSpaceRequestForm(forms.ModelForm):
    class Meta:
        model = ForumSpaceRequest
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
            organizations = approved_member_organizations(user)
        self.fields["requested_by_org"].queryset = organizations
        self.fields["requested_by_org"].required = False


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["body"]
        labels = {
            "body": "Post",
        }
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a post to this forum"}),
        }
