from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from storage.models import StorageLocation

from .forms import DonationFoodItemFormSet, DonationForm, FoodRequestForm
from .models import Donation, DonationFoodItem

PICKUP_END_HOURS = {
    Donation.PickupEndTime.BEFORE_2PM: 14,
    Donation.PickupEndTime.BEFORE_3PM: 15,
    Donation.PickupEndTime.BEFORE_4PM: 16,
    Donation.PickupEndTime.BEFORE_5PM: 17,
}


def set_pickup_deadline_from_pickup_fields(donation):
    pickup_date = timezone.localdate()
    if donation.pickup_day == Donation.PickupDay.TOMORROW:
        pickup_date += timedelta(days=1)

    end_hour = PICKUP_END_HOURS.get(donation.pickup_end_time, 17)
    donation.pickup_deadline = timezone.make_aware(datetime.combine(pickup_date, time(end_hour)))


def sync_donation_summary_from_items(donation):
    first_item = donation.food_items.first()
    if first_item is None:
        return

    donation.food_category = first_item.food_category
    donation.food_type = list(donation.food_items.values_list("food_category", flat=True).distinct())
    donation.quantity = first_item.quantity
    donation.unit = first_item.packaging
    donation.save(update_fields=["food_category", "food_type", "quantity", "unit"])


def save_food_items(donation, formset):
    donation.food_items.all().delete()

    items = []
    for form in formset:
        if not form.cleaned_data.get("selected"):
            continue

        items.append(
            DonationFoodItem(
                donation=donation,
                food_category=form.cleaned_data["food_category"],
                packaging=form.cleaned_data["packaging"],
                quantity=form.cleaned_data["quantity"],
                description=form.cleaned_data["description"],
            ),
        )

    DonationFoodItem.objects.bulk_create(items)


def user_organization(user):
    if not user.is_authenticated:
        return None
    return user.organizations.filter(is_active=True).first()


def donor_profile(request, organization):
    full_name = request.user.get_full_name().strip()
    address_parts = []
    if organization:
        region_and_postal = " ".join(part for part in [organization.region, organization.postal_code] if part)
        address_parts = [
            organization.address_line_1,
            organization.address_line_2,
            organization.municipality,
            region_and_postal,
        ]

    return {
        "company_name": organization.name if organization else "",
        "address_1": organization.address_line_1 if organization else "",
        "address_2": organization.address_line_2 if organization else "",
        "address_display": ", ".join(part for part in address_parts if part),
        "city": organization.municipality if organization else "",
        "province_or_state": organization.region if organization else "",
        "postal_code": organization.postal_code if organization else "",
        "donor_name": full_name or request.user.email,
        "donor_contact": request.user.email,
        "contact_email": organization.email if organization and organization.email else request.user.email,
        "contact_phone": str(organization.phone) if organization and organization.phone else "",
    }


def request_account_initial(request):
    if not request.user.is_authenticated:
        return {}

    full_name = request.user.get_full_name().strip()
    initial = {
        "email": request.user.email,
        "receiver_name": full_name or request.user.email,
    }
    organization = user_organization(request.user)
    if organization is not None:
        initial["organization"] = organization.name
    return initial


@login_required
def donation_list(request):
    donations = Donation.objects.all().order_by("-created_at")
    organization = user_organization(request.user)

    if request.user.is_authenticated and not request.user.is_staff:
        donations = donations.filter(supplier_organization=organization)

    status = request.GET.get("status")
    storage_requirement = request.GET.get("storage_requirement")

    if status:
        donations = donations.filter(status=status)

    if storage_requirement:
        donations = donations.filter(storage_requirement=storage_requirement)

    context = {
        "donations": donations,
        "status_choices": Donation.Status.choices,
        "storage_requirement_choices": Donation.StorageRequirement.choices,
    }

    return render(request, "donations/donation_list.html", context)


@login_required
def donation_create(request):
    organization = user_organization(request.user)

    if request.method == "POST":
        form = DonationForm(request.POST)
        formset = DonationFoodItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            donation = form.save(commit=False)
            donation.status = Donation.Status.SUBMITTED
            donation.food_category = Donation.FoodCategory.OTHER
            donation.food_type = []
            donation.quantity = 1
            donation.unit = Donation.QuantityUnit.ITEMS
            donation.submitted_by = request.user
            donation.supplier_organization = organization
            set_pickup_deadline_from_pickup_fields(donation)
            donation.save()
            save_food_items(donation, formset)
            sync_donation_summary_from_items(donation)
            return redirect("donations:detail", pk=donation.pk)
    else:
        form = DonationForm()
        formset = DonationFoodItemFormSet()

    return render(
        request,
        "donations/donation_form.html",
        {
            "form": form,
            "formset": formset,
            "donor_profile": donor_profile(request, organization),
            "supplier_organization": organization,
            "title": "Create Donation",
        },
    )


@login_required
def donation_edit(request, pk):
    donation = get_object_or_404(Donation, pk=pk)

    if request.method == "POST":
        form = DonationForm(request.POST, instance=donation)
        formset = DonationFoodItemFormSet(request.POST, donation=donation)
        if form.is_valid() and formset.is_valid():
            donation = form.save(commit=False)
            if request.user.is_authenticated and donation.submitted_by_id is None:
                donation.submitted_by = request.user
            if request.user.is_authenticated and donation.supplier_organization_id is None:
                donation.supplier_organization = user_organization(request.user)
            set_pickup_deadline_from_pickup_fields(donation)
            donation.save()
            save_food_items(donation, formset)
            sync_donation_summary_from_items(donation)
            return redirect("donations:detail", pk=donation.pk)
    else:
        form = DonationForm(instance=donation)
        formset = DonationFoodItemFormSet(donation=donation)

    return render(
        request,
        "donations/donation_form.html",
        {
            "form": form,
            "formset": formset,
            "donor_profile": donor_profile(request, donation.supplier_organization),
            "supplier_organization": donation.supplier_organization,
            "title": "Edit Donation",
        },
    )


@login_required
def donation_detail(request, pk):
    donation = get_object_or_404(Donation, pk=pk)

    matching_storage = StorageLocation.objects.filter(
        is_active=True,
        approval_status=StorageLocation.ApprovalStatus.APPROVED,
        capacity_status=StorageLocation.CapacityStatus.AVAILABLE,
    )

    if donation.storage_requirement != Donation.StorageRequirement.NONE:
        matching_storage = matching_storage.filter(
            storage_type=donation.storage_requirement,
        )

    matching_storage = matching_storage.filter(
        available_space__gte=donation.quantity,
    )

    return render(
        request,
        "donations/donation_detail.html",
        {
            "donation": donation,
            "matching_storage": matching_storage,
        },
    )


def donation_assign_storage(request, pk, storage_pk):
    donation = get_object_or_404(Donation, pk=pk)
    storage_location = get_object_or_404(StorageLocation, pk=storage_pk)

    donation.assign_storage(storage_location)

    return redirect("donations:detail", pk=donation.pk)


def available_donation_list(request):
    donations = Donation.objects.exclude(
        status__in=[
            Donation.Status.DRAFT,
            Donation.Status.CANCELLED,
            Donation.Status.EXPIRED,
            Donation.Status.COMPLETED,
        ],
    ).order_by("-created_at")

    return render(request, "donations/available_donation_list.html", {"donations": donations})


def available_donation_detail(request, pk):
    donation = get_object_or_404(Donation, pk=pk)

    return render(request, "donations/available_donation_detail.html", {"donation": donation})


def food_request_create(request, pk):
    donation = get_object_or_404(Donation, pk=pk)

    if request.method == "POST":
        form = FoodRequestForm(request.POST)
        if form.is_valid():
            food_request = form.save(commit=False)
            food_request.donation = donation
            if request.user.is_authenticated:
                food_request.requested_by = request.user
                food_request.receiver_organization = user_organization(request.user)
            food_request.save()
            return redirect("donations:request_thanks", pk=food_request.pk)
    else:
        form = FoodRequestForm(initial=request_account_initial(request))

    return render(request, "donations/food_request_form.html", {"form": form, "donation": donation})


def food_request_thanks(request, pk):
    return render(request, "donations/food_request_thanks.html", {"request_id": pk})
