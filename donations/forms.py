from django import forms

from storage.models import StorageLocation

from .models import Donation, DonationFoodItem, FoodRequest

INPUT_CLASS = "input input-bordered w-full"
SELECT_CLASS = "select select-bordered w-full"
TEXTAREA_CLASS = "textarea textarea-bordered w-full"
CHECKBOX_CLASS = "checkbox checkbox-primary"

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


class DonationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control_classes(self.fields)

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


class DonationFoodItemIntakeForm(forms.Form):
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
        apply_form_control_classes(self.fields)

    def clean(self):
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
    def __init__(self, *args, **kwargs):
        donation = kwargs.pop("donation", None)
        initial = kwargs.pop("initial", None)
        if initial is None:
            initial = get_food_item_initial(donation)
        super().__init__(*args, initial=initial, prefix="food_items", **kwargs)

        for form, (_, label, example) in zip(self.forms, FOOD_TYPE_INTAKE, strict=False):
            form.food_label = label
            form.food_example = example

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        if not any(form.cleaned_data.get("selected") for form in self.forms):
            raise forms.ValidationError("Select at least one food type.")


def get_food_item_initial(donation=None):
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


class FoodRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_control_classes(self.fields)
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


class FoodRequestAllocationForm(forms.Form):
    food_item_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(required=False, min_value=0, label="Quantity requested")

    def __init__(self, *args, **kwargs):
        self.food_item = kwargs.pop("food_item", None)
        super().__init__(*args, **kwargs)
        apply_form_control_classes(self.fields)

    def clean_quantity(self):
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
    def __init__(self, *args, **kwargs):
        self.donation = kwargs.pop("donation")
        initial = [
            {
                "food_item_id": food_item.id,
                "quantity": None,
            }
            for food_item in self.donation.food_items.all()
        ]
        super().__init__(*args, initial=initial, prefix="allocations", **kwargs)

        food_items = list(self.donation.food_items.all())
        for form, food_item in zip(self.forms, food_items, strict=False):
            form.food_item = food_item

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        if not any(form.cleaned_data.get("quantity", 0) > 0 for form in self.forms):
            raise forms.ValidationError("Request at least one food item.")


def apply_form_control_classes(fields):
    for field in fields.values():
        widget = field.widget
        existing_class = widget.attrs.get("class", "")

        if isinstance(widget, forms.RadioSelect):
            continue
        elif isinstance(widget, forms.CheckboxInput):
            css_class = CHECKBOX_CLASS
        elif isinstance(widget, forms.Select):
            css_class = SELECT_CLASS
        elif isinstance(widget, forms.Textarea):
            css_class = TEXTAREA_CLASS
        elif isinstance(widget, forms.HiddenInput):
            continue
        else:
            css_class = INPUT_CLASS

        widget.attrs["class"] = f"{existing_class} {css_class}".strip()
