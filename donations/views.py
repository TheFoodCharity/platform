from datetime import datetime, time, timedelta

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


def donation_list(request):
    donations = Donation.objects.all().order_by("-created_at")

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


def donation_create(request):
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
        {"form": form, "formset": formset, "title": "Create Donation"},
    )


def donation_edit(request, pk):
    donation = get_object_or_404(Donation, pk=pk)

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
        {"form": form, "formset": formset, "title": "Edit Donation"},
    )


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
            food_request.save()
            return redirect("donations:request_thanks", pk=food_request.pk)
    else:
        form = FoodRequestForm()

    return render(request, "donations/food_request_form.html", {"form": form, "donation": donation})


def food_request_thanks(request, pk):
    return render(request, "donations/food_request_thanks.html", {"request_id": pk})
