from django import forms

from storage.models import StorageLocation

from .models import FoodRequest


class FoodRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferred_storage"].queryset = StorageLocation.objects.filter(
            is_active=True,
            approval_status=StorageLocation.ApprovalStatus.APPROVED,
        ).exclude(
            capacity_status__in=[
                StorageLocation.CapacityStatus.FULL,
                StorageLocation.CapacityStatus.UNAVAILABLE,
            ],
        )

    class Meta:
        model = FoodRequest
        fields = [
            "receiver_name",
            "organization",
            "email",
            "phone",
            "requested_quantity",
            "requested_unit",
            "storage_required",
            "preferred_storage",
            "storage_notes",
            "notes",
        ]
        widgets = {
            "storage_notes": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
