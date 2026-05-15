from crispy_forms.layout import Div, Fieldset, Layout
from django import forms

from organizations.models import Organization
from storage.models import StorageLocation
from theme.forms import ThemedFormMixin

from .models import Donation, DonationFoodItem, FoodRequest

FOOD_TYPE_INTAKE = [
    (Donation.FoodCategory.BAKED_GOODS, "Baked Goods", "e.g. Bread, pastries"),
    (Donation.FoodCategory.DAIRY, "Dairy", "e.g. Milk, cheese"),
    (Donation.FoodCategory.MEAT_PROTEIN, "Meat & Protein", "e.g. Beef, chicken, eggs"),
    (Donation.FoodCategory.NON_FOOD, "Non-Food", "e.g. Latex gloves, disposable cups, etc."),
    (Donation.FoodCategory.NON_PERISHABLE, "Non-Perishable", "e.g. Canned vegetables, granola bars, uncooked pasta"),
    (Donation.FoodCategory.OTHER, "Other", "e.g. Water, seedlings, etc."),
    (Donation.FoodCategory.PREPARED_INDIVIDUAL, "Prepared - Individually Packaged", "e.g. Sandwiches"),
    (Donation.FoodCategory.PREPARED_TRAYS, "Prepared - Trays/Multi-Serving", "e.g. Lasagna"),
    (Donation.FoodCategory.PRODUCE, "Produce", "e.g. Peppers, eggplant"),
]


class DonationForm(ThemedFormMixin, forms.ModelForm):
    """Main supplier intake form; food item quantities are captured by a separate formset."""

    # Keep the custom donation page on crispy forms while preserving its sectioned workflow.
    layout = Layout(
        Fieldset(
            "Pickup Details",
            Div(
                Div("pickup_location", css_class="md:col-span-2"),
                Div("pickup_day", css_class="md:col-span-2"),
                "pickup_ready_time",
                "pickup_end_time",
                Div("pickup_notes", css_class="md:col-span-2"),
                css_class="grid gap-5 md:grid-cols-2",
            ),
        ),
        Fieldset(
            "Receiver Preferences",
            "receiver_limit",
            "preferred_receiver_organization",
        ),
        Fieldset(
            "Logistics",
            "storage_requirement",
            "fits_in_car",
            Div(
                "requires_van",
                "requires_cube_van",
                "requires_refrigerated_vehicle",
                "requires_pallet_jack",
                "requires_forklift",
                "loading_dock_available",
                "donor_can_help_load",
                css_class="grid gap-4 md:grid-cols-2",
            ),
        ),
        Fieldset(
            "Food Safety",
            "food_safety_agreement",
        ),
        Fieldset(
            "Other Information",
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
        self.fields["preferred_receiver_organization"].queryset = Organization.objects.filter(
            is_active=True,
        ).order_by("name")
        self.fields["preferred_receiver_organization"].empty_label = "No preferred receiver"

    def clean_food_safety_agreement(self):
        agreed = self.cleaned_data["food_safety_agreement"]
        if not agreed:
            raise forms.ValidationError("You must confirm the donation meets food safety standards.")
        return agreed

    class Meta:
        model = Donation

        fields = [
            "pickup_location",
            "pickup_day",
            "pickup_ready_time",
            "pickup_end_time",
            "pickup_notes",
            "storage_requirement",
            "receiver_limit",
            "preferred_receiver_organization",
            "requires_van",
            "requires_cube_van",
            "requires_refrigerated_vehicle",
            "requires_pallet_jack",
            "requires_forklift",
            "loading_dock_available",
            "donor_can_help_load",
            "people_fed_estimate",
            "fits_in_car",
            "food_safety_agreement",
            "other_information",
        ]

        widgets = {
            "pickup_day": forms.RadioSelect(),
            "fits_in_car": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            "food_safety_agreement": forms.CheckboxInput(),
            "other_information": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "receiver_limit": "Maximum number of receivers",
            "preferred_receiver_organization": "Preferred receiver",
        }


class DonationFoodItemIntakeForm(ThemedFormMixin, forms.Form):
    """One selectable food category row in the donation intake formset."""

    layout = Layout(
        "food_category",
        "selected",
        Div(
            "packaging",
            "quantity",
            "description",
            css_class="donation-food-type-details mt-4 hidden rounded-xl border border-primary/20 bg-primary/5 p-5",
        ),
    )

    selected = forms.BooleanField(required=False)
    food_category = forms.ChoiceField(choices=Donation.FoodCategory.choices, widget=forms.HiddenInput)
    packaging = forms.ChoiceField(
        choices=[("", "Choose packaging"), *DonationFoodItem.Packaging.choices],
        required=False,
        label="How is it packaged?",
    )
    quantity = forms.IntegerField(required=False, min_value=1, label="How many?")
    description = forms.CharField(required=False, label="Describe it:")

    def __init__(self, *args, **kwargs):
        self.food_label = kwargs.pop("food_label", "")
        self.food_example = kwargs.pop("food_example", "")
        super().__init__(*args, **kwargs)

    def clean(self):
        """Treat any entered package details as selecting that food type."""
        cleaned_data = super().clean()
        selected = cleaned_data.get("selected")
        packaging = cleaned_data.get("packaging")
        quantity = cleaned_data.get("quantity")
        description = cleaned_data.get("description")

        if packaging or quantity or description:
            selected = True
            cleaned_data["selected"] = True

        if selected:
            if not packaging:
                self.add_error("packaging", "Choose how this food is packaged.")
            if quantity is None:
                self.add_error("quantity", "Enter how many packages are available.")

        return cleaned_data


BaseDonationFoodItemFormSet = forms.formset_factory(
    DonationFoodItemIntakeForm,
    extra=0,
    min_num=1,
    validate_min=False,
)


class DonationFoodItemFormSet(BaseDonationFoodItemFormSet):
    """Build the fixed list of supported donation food categories."""

    def __init__(self, *args, **kwargs):
        donation = kwargs.pop("donation", None)
        initial = kwargs.pop("initial", None)
        if initial is None:
            initial = get_food_item_initial(donation)
        super().__init__(*args, initial=initial, prefix="food_items", **kwargs)

        for form, (_, label, example) in zip(self.forms, FOOD_TYPE_INTAKE, strict=False):
            form.food_label = label
            form.food_example = example
            form.fields["selected"].label = f"{label} ({example})"

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        if not any(form.cleaned_data.get("selected") for form in self.forms):
            raise forms.ValidationError("Select at least one food type.")


def get_food_item_initial(donation=None):
    """Prefill the fixed food category list when editing an existing donation."""
    existing_items = {}
    if donation is not None and donation.pk:
        existing_items = {item.food_category: item for item in donation.food_items.all()}

    initial = []
    for value, _label, _example in FOOD_TYPE_INTAKE:
        item = existing_items.get(value)
        initial.append(
            {
                "selected": item is not None,
                "food_category": value,
                "packaging": item.packaging if item else "",
                "quantity": item.quantity if item else None,
                "description": item.description if item else "",
            },
        )
    return initial


class FoodRequestForm(ThemedFormMixin, forms.ModelForm):
    """Receiver request details outside of per-item quantity allocation."""

    layout = Layout(
        "storage_required",
        Div(
            "preferred_storage",
            "storage_notes",
            css_class="mt-5 grid gap-5 md:grid-cols-2",
        ),
        "notes",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "storage_required"
        ].help_text = "Select this if you need third-party storage before receiving the food."
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
            "storage_required",
            "preferred_storage",
            "storage_notes",
            "notes",
        ]
        widgets = {
            "storage_notes": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }


class FoodRequestAllocationForm(ThemedFormMixin, forms.Form):
    """One quantity input for a food item available on a donation."""

    layout = Layout("food_item_id", "quantity")

    food_item_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(required=False, min_value=0, label="Quantity requested")

    def __init__(self, *args, **kwargs):
        self.food_item = kwargs.pop("food_item", None)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        """Prevent receivers from requesting more than the current remaining quantity."""
        quantity = self.cleaned_data["quantity"] or 0
        if self.food_item is not None and quantity > self.food_item.remaining_quantity:
            raise forms.ValidationError(
                f"Only {self.food_item.remaining_quantity} {self.food_item.get_packaging_display()} remaining.",
            )
        return quantity


BaseFoodRequestAllocationFormSet = forms.formset_factory(
    FoodRequestAllocationForm,
    extra=0,
    min_num=1,
    validate_min=False,
)


class FoodRequestAllocationFormSet(BaseFoodRequestAllocationFormSet):
    """Create one allocation input per food item in the selected donation."""

    def __init__(self, *args, **kwargs):
        self.donation = kwargs.pop("donation")
        self.force_remaining = kwargs.pop("force_remaining", False)
        initial = [
            {
                "food_item_id": food_item.id,
                "quantity": food_item.remaining_quantity if self.force_remaining else None,
            }
            for food_item in self.donation.food_items.all()
        ]
        super().__init__(*args, initial=initial, prefix="allocations", **kwargs)

        food_items = list(self.donation.food_items.all())
        for form, food_item in zip(self.forms, food_items, strict=False):
            form.food_item = food_item
            if self.force_remaining:
                form.fields["quantity"].disabled = True
                form.fields["quantity"].help_text = "Please collect remaining quantity"

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        if not any(form.cleaned_data.get("quantity", 0) > 0 for form in self.forms):
            raise forms.ValidationError("Request at least one food item.")
