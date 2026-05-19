from datetime import datetime, time, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from organizations.decorators import organization_required

from .forms import DonationFoodItemFormSet, DonationForm, FoodRequestAllocationFormSet, FoodRequestForm
from .models import Donation, DonationFoodItem, FoodRequest, FoodRequestAllocation

PICKUP_END_HOURS = {
    Donation.PickupEndTime.BEFORE_2PM: 14,
    Donation.PickupEndTime.BEFORE_3PM: 15,
    Donation.PickupEndTime.BEFORE_4PM: 16,
    Donation.PickupEndTime.BEFORE_5PM: 17,
}


def require_permission(request, code, obj=None):
    """Raise a standard 403 when the donation permission cascade denies access."""
    if not request.user.has_perm(code, obj):
        raise PermissionDenied()


def expire_past_deadline_donations():
    """Expire open donations once their pickup deadline has passed."""
    start_of_today = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
    Donation.objects.filter(
        pickup_deadline__lt=start_of_today,
        status__in=[
            Donation.Status.SUBMITTED,
            Donation.Status.AVAILABLE,
        ],
    ).update(status=Donation.Status.EXPIRED, updated_at=timezone.now())


def set_pickup_deadline_from_pickup_fields(donation):
    """Convert the selected pickup day/end window into a concrete deadline."""
    pickup_date = timezone.localdate()
    if donation.pickup_day == Donation.PickupDay.TOMORROW:
        pickup_date += timedelta(days=1)

    end_hour = PICKUP_END_HOURS.get(donation.pickup_end_time, 17)
    donation.pickup_deadline = timezone.make_aware(datetime.combine(pickup_date, time(end_hour)))


def sync_donation_summary_from_items(donation):
    """Update denormalized donation summary fields from the saved food items."""
    first_item = donation.food_items.first()
    if first_item is None:
        return

    # Keep legacy summary columns aligned for admin lists and older templates.
    donation.food_category = first_item.food_category
    donation.food_type = list(donation.food_items.values_list("food_category", flat=True).distinct())
    donation.quantity = sum(donation.food_items.values_list("quantity", flat=True))
    donation.unit = first_item.packaging
    donation.save(update_fields=["food_category", "food_type", "quantity", "unit"])


def save_food_items(donation, formset):
    """Replace a donation's food item rows from the selected intake formset rows."""
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


def donor_profile(request, organization):
    """Shape account and organization data for the read-only donor summary panel."""
    full_name = request.user.get_full_name().strip()
    address_display = organization_address_display(organization)

    return {
        "company_name": organization.name if organization else "",
        "address_1": organization.address_line_1 if organization else "",
        "address_2": organization.address_line_2 if organization else "",
        "address_display": address_display,
        "city": organization.municipality if organization else "",
        "province_or_state": organization.region if organization else "",
        "postal_code": organization.postal_code if organization else "",
        "donor_name": full_name or request.user.email,
        "donor_contact": request.user.email,
        "contact_email": organization.email if organization and organization.email else request.user.email,
        "contact_phone": str(organization.phone) if organization and organization.phone else "",
    }


def organization_address_display(organization):
    """Format an organization address for pickup-location defaults."""
    if organization is None:
        return ""

    region_and_postal = " ".join(part for part in [organization.region, organization.postal_code] if part)
    address_parts = [
        organization.address_line_1,
        organization.address_line_2,
        organization.municipality,
        region_and_postal,
    ]

    return ", ".join(part for part in address_parts if part)


def receiver_profile(request, organization):
    """Shape account and organization data for the read-only receiver summary panel."""
    full_name = request.user.get_full_name().strip()
    return {
        "email": request.user.email,
        "receiver_name": full_name or request.user.email,
        "organization": organization.name if organization else "",
        "phone": str(organization.phone) if organization and organization.phone else "",
    }


def save_food_request_allocations(food_request, formset):
    """Persist the requested quantities for each selected donation food item."""
    allocations = []
    food_items = {item.id: item for item in food_request.donation.food_items.all()}

    for form in formset:
        quantity = form.cleaned_data.get("quantity") or 0
        if quantity <= 0:
            continue

        food_item = food_items[form.cleaned_data["food_item_id"]]
        allocations.append(
            FoodRequestAllocation(
                food_request=food_request,
                donation_food_item=food_item,
                quantity=quantity,
            ),
        )

    FoodRequestAllocation.objects.bulk_create(allocations)
    sync_donation_status_from_allocations(food_request.donation)


def sync_donation_status_from_allocations(donation):
    """Mark a donation completed once every food item has been fully requested."""
    if donation.is_fully_requested and donation.status != Donation.Status.COMPLETED:
        donation.status = Donation.Status.COMPLETED
        donation.save(update_fields=["status", "updated_at"])


@organization_required
def donation_list(request):
    require_permission(request, "donations.view_donations")
    expire_past_deadline_donations()
    donations = Donation.objects.all().order_by("-created_at")
    organization = request.organization

    if not request.user.is_staff:
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


@organization_required
def donation_create(request):
    require_permission(request, "donations.create_donation")
    organization = request.organization

    if request.method == "POST":
        form = DonationForm(request.POST)
        formset = DonationFoodItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            donation = form.save(commit=False)
            donation.status = Donation.Status.AVAILABLE
            donation.food_category = Donation.FoodCategory.OTHER
            donation.food_type = []
            donation.quantity = 1
            donation.unit = Donation.QuantityUnit.BOXES
            donation.submitted_by = request.user
            donation.supplier_organization = organization
            set_pickup_deadline_from_pickup_fields(donation)
            donation.save()
            save_food_items(donation, formset)
            sync_donation_summary_from_items(donation)
            return redirect("donations:donation_thanks", pk=donation.pk)
    else:
        form = DonationForm(initial={"pickup_location": organization_address_display(organization)})
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


@organization_required
def donation_edit(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    require_permission(request, "donations.edit_donation", donation)

    if request.method == "POST":
        form = DonationForm(request.POST, instance=donation)
        formset = DonationFoodItemFormSet(request.POST, donation=donation)
        if form.is_valid() and formset.is_valid():
            donation = form.save(commit=False)
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


@organization_required
def donation_detail(request, pk):
    expire_past_deadline_donations()
    donation = get_object_or_404(
        Donation.objects.select_related(
            "submitted_by",
            "supplier_organization",
        ).prefetch_related(
            "food_items",
            "food_requests__requested_by",
            "food_requests__receiver_organization",
            "food_requests__allocations__donation_food_item",
        ),
        pk=pk,
    )
    require_permission(request, "donations.view_donation_detail", donation)

    return render(
        request,
        "donations/donation_detail.html",
        {
            "donation": donation,
        },
    )


@organization_required
def available_donation_list(request):
    require_permission(request, "donations.view_available_donations")
    expire_past_deadline_donations()
    donations = (
        Donation.objects.exclude(
            status__in=[
                Donation.Status.CANCELLED,
                Donation.Status.EXPIRED,
                # Donation.Status.COMPLETED,
            ],
        )
        .prefetch_related(
            "food_items",
            "food_items__request_allocations__food_request",
        )
        .select_related(
            "supplier_organization",
            "submitted_by",
            "preferred_receiver_organization",
        )
        .order_by("-created_at")
    )

    category = request.GET.get("category")
    availability = request.GET.get("availability")

    if category:
        donations = donations.filter(food_items__food_category=category).distinct()

    donation_list = list(donations)
    if availability == "available":
        donation_list = [donation for donation in donation_list if not donation.is_fully_requested]
    elif availability == "fully_requested":
        donation_list = [donation for donation in donation_list if donation.is_fully_requested]

    receiver_organization = request.organization
    for donation in donation_list:
        donation.is_preferred_receiver_match = donation.preferred_receiver_organization_id == receiver_organization.id
    donation_list.sort(key=lambda donation: not donation.is_preferred_receiver_match)

    return render(
        request,
        "donations/available_donation_list.html",
        {
            "donations": donation_list,
            "category_choices": Donation.FoodCategory.choices,
            "availability": availability,
            "category": category,
        },
    )


@organization_required
def available_donation_detail(request, pk):
    require_permission(request, "donations.view_available_donations")
    expire_past_deadline_donations()
    donation = get_object_or_404(
        Donation.objects.select_related(
            "submitted_by",
            "supplier_organization",
        ).prefetch_related(
            "food_items",
            "food_items__request_allocations__food_request",
        ),
        pk=pk,
    )

    return render(request, "donations/available_donation_detail.html", {"donation": donation})


@organization_required
def food_request_create(request, pk):
    require_permission(request, "donations.request_donation")
    expire_past_deadline_donations()
    donation = get_object_or_404(Donation, pk=pk)
    organization = request.organization
    if not donation.can_accept_receiver(organization):
        messages.error(request, "This donation has reached its maximum number of receivers.")
        return redirect("donations:available_detail", pk=donation.pk)
    if donation.status == Donation.Status.EXPIRED:
        messages.error(request, "This donation has expired and can no longer be requested.")
        return redirect("donations:available_detail", pk=donation.pk)

    force_remaining = donation.is_final_receiver_slot(organization)

    if request.method == "POST":
        form = FoodRequestForm(request.POST)
        formset = FoodRequestAllocationFormSet(request.POST, donation=donation, force_remaining=force_remaining)
        if form.is_valid() and formset.is_valid():
            food_request = form.save(commit=False)
            food_request.donation = donation
            food_request.requested_by = request.user
            food_request.receiver_organization = organization
            food_request.save()
            save_food_request_allocations(food_request, formset)
            return redirect("donations:request_thanks", pk=food_request.pk)
    else:
        form = FoodRequestForm()
        formset = FoodRequestAllocationFormSet(donation=donation, force_remaining=force_remaining)

    return render(
        request,
        "donations/food_request_form.html",
        {
            "form": form,
            "formset": formset,
            "donation": donation,
            "receiver_profile": receiver_profile(request, organization),
            "force_remaining": force_remaining,
        },
    )


@organization_required
def food_request_detail(request, pk):
    food_request = get_object_or_404(
        FoodRequest.objects.select_related(
            "donation",
            "donation__supplier_organization",
            "requested_by",
            "receiver_organization",
        ).prefetch_related(
            "allocations__donation_food_item",
        ),
        pk=pk,
    )
    require_permission(request, "donations.view_food_request", food_request)
    return render(
        request,
        "donations/food_request_detail.html",
        {
            "food_request": food_request,
            "receiver_address_display": organization_address_display(food_request.receiver_organization),
        },
    )


@organization_required
def food_request_thanks(request, pk):
    food_request = get_object_or_404(FoodRequest.objects.select_related("donation"), pk=pk)
    require_permission(request, "donations.view_food_request", food_request)
    return render(request, "donations/food_request_thanks.html", {"food_request": food_request})


@organization_required
def donation_thanks(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    require_permission(request, "donations.view_donation_detail", donation)
    return render(request, "donations/donation_thanks.html", {"donation": donation})
