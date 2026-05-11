from crispy_forms.layout import Div, Fieldset, Layout, Row
from django import forms

from storage.models import StorageLocation
from theme.forms import ThemedFormMixin

from .models import Donation, DonationFoodItem, FoodRequest


class DonationForm(ThemedFormMixin, forms.ModelForm):
    layout = Layout(
        Fieldset(
            "Donor Information",
            Row(
                "company_name",
                "donor_name",
                Div("address_1", css_class="md:col-span-2"),
                Div("address_2", css_class="md:col-span-2"),
                "city",
                "province_or_state",
                "postal_code",
                "donor_contact",
                "contact_email",
                "contact_phone",
            ),
        ),
        Fieldset(
            "Pickup Details",
            Row(
                Div("pickup_location", css_class="md:col-span-2"),
                Div("pickup_day", css_class="md:col-span-2"),
                "pickup_ready_time",
                "pickup_end_time",
                "pickup_window",
            ),
        ),
        Fieldset(
            "Logistics",
            Row(
                "storage_requirement",
                "fits_in_car",
                "requires_van",
                "requires_cube_van",
                "requires_refrigerated_vehicle",
                "requires_pallet_jack",
                "requires_forklift",
                "loading_dock_available",
                "donor_can_help_load",
            ),
            "people_fed_estimate",
        ),
        Fieldset(
            "Food Safety",
            "food_safety_agreement",
        ),
        Fieldset(
            "Other Information",
            "special_handling_notes",
            "chain_of_custody_notes",
            "other_information",
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "food_safety_agreement"
        ].help_text = (
            "The food is safe for human consumption, has been stored properly, and has not been served from a buffet."
        )

    def clean_food_safety_agreement(self):
        agreed = self.cleaned_data["food_safety_agreement"]
        if not agreed:
            raise forms.ValidationError("You must confirm the donation meets food safety standards.")
        return agreed

    class Meta:
        model = Donation

        fields = [
            "company_name",
            "address_1",
            "address_2",
            "city",
            "province_or_state",
            "postal_code",
            "donor_name",
            "donor_contact",
            "contact_email",
            "contact_phone",
            "pickup_location",
            "pickup_day",
            "pickup_ready_time",
            "pickup_end_time",
            "pickup_window",
            "storage_requirement",
            "requires_van",
            "requires_cube_van",
            "requires_refrigerated_vehicle",
            "requires_pallet_jack",
            "requires_forklift",
            "loading_dock_available",
            "donor_can_help_load",
            "special_handling_notes",
            "chain_of_custody_notes",
            "people_fed_estimate",
            "fits_in_car",
            "food_safety_agreement",
            "other_information",
        ]

        widgets = {
            "pickup_day": forms.RadioSelect(),
            "fits_in_car": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            "food_safety_agreement": forms.CheckboxInput(),
            "special_handling_notes": forms.Textarea(attrs={"rows": 4}),
            "chain_of_custody_notes": forms.Textarea(attrs={"rows": 4}),
            "other_information": forms.Textarea(attrs={"rows": 4}),
        }


class DonationFoodItemForm(ThemedFormMixin, forms.ModelForm):
    layout = Layout(
        Row("food_category", "packaging"),
        Row("quantity", "description"),
    )

    class Meta:
        model = DonationFoodItem
        fields = ["food_category", "packaging", "quantity", "description"]


DonationFoodItemFormSet = forms.inlineformset_factory(
    Donation,
    DonationFoodItem,
    form=DonationFoodItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=20,
    validate_max=True,
)


class FoodRequestForm(ThemedFormMixin, forms.ModelForm):
    layout = Layout(
        Row("receiver_name", "organization", "email", "phone"),
        Row("requested_quantity", "requested_unit"),
        Fieldset(
            "Storage",
            "storage_required",
            "preferred_storage",
            "storage_notes",
        ),
        "notes",
    )

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
