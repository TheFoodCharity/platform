from django import forms

from .models import DonationTicket


class DonationTicketForm(forms.ModelForm):
    class Meta:
        model = DonationTicket

        fields = [
            "donor_name",
            "donor_contact",
            "food_category",
            "food_type",
            "quantity",
            "unit",
            "estimated_weight",
            "pickup_location",
            "pickup_window",
            "pickup_deadline",
            "best_before_date",
            "storage_requirement",
            "temperature_requirement",
            "requires_van",
            "requires_cube_van",
            "requires_refrigerated_vehicle",
            "requires_pallet_jack",
            "requires_forklift",
            "loading_dock_available",
            "donor_can_help_load",
            "special_handling_notes",
            "chain_of_custody_notes",
            "assigned_storage",
            "status",
        ]

        widgets = {
            "pickup_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "best_before_date": forms.DateInput(attrs={"type": "date"}),
        }
