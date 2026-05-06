from django.shortcuts import get_object_or_404, redirect, render

from .forms import StorageLocationForm
from .models import StorageLocation


def storage_list(request):
    locations = StorageLocation.objects.filter(is_active=True).order_by("name")

    storage_type = request.GET.get("storage_type")
    municipality = request.GET.get("municipality")
    region = request.GET.get("region")
    capacity_status = request.GET.get("capacity_status")

    if storage_type:
        locations = locations.filter(storage_type=storage_type)

    if municipality:
        locations = locations.filter(municipality__icontains=municipality)

    if region:
        locations = locations.filter(region__icontains=region)

    if capacity_status:
        locations = locations.filter(capacity_status=capacity_status)

    context = {
        "locations": locations,
        "storage_type_choices": StorageLocation.StorageType.choices,
        "capacity_status_choices": StorageLocation.CapacityStatus.choices,
    }

    return render(request, "storage/storage_list.html", context)


def storage_create(request):
    if request.method == "POST":
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            storage_location = form.save()
            storage_location.update_capacity_status()
            return redirect("storage:list")
    else:
        form = StorageLocationForm()

    return render(
        request,
        "storage/storage_form.html",
        {"form": form, "title": "Add Storage Location"},
    )


def storage_edit(request, pk):
    location = get_object_or_404(StorageLocation, pk=pk)

    if request.method == "POST":
        form = StorageLocationForm(request.POST, instance=location)
        if form.is_valid():
            storage_location = form.save()
            storage_location.update_capacity_status()
            return redirect("storage:list")
    else:
        form = StorageLocationForm(instance=location)

    return render(
        request,
        "storage/storage_form.html",
        {"form": form, "title": "Edit Storage Location"},
    )


def storage_detail(request, pk):
    location = get_object_or_404(StorageLocation, pk=pk)

    return render(
        request,
        "storage/storage_detail.html",
        {"location": location},
    )