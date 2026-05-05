# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StorageLocationForm
from .models import StorageLocation


def storage_list(request):
    locations = StorageLocation.objects.all()
    return render(request, "storage/storage_list.html", {"locations": locations})


def storage_create(request):
    if request.method == "POST":
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("storage:list")
    else:
        form = StorageLocationForm()

    return render(request, "storage/storage_form.html", {"form": form, "title": "Add Storage Location"})


def storage_edit(request, pk):
    location = get_object_or_404(StorageLocation, pk=pk)

    if request.method == "POST":
        form = StorageLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect("storage:list")
    else:
        form = StorageLocationForm(instance=location)

    return render(request, "storage/storage_form.html", {"form": form, "title": "Edit Storage Location"})
