from django.shortcuts import render

from .forms import FoodDonationForm


def home(request):
    return render(request, "public/home.html")


def donate_food(request):
    form = FoodDonationForm(request.POST if request.method == "POST" else None)
    submitted = False

    if request.method == "POST" and form.is_valid():
        submitted = True
        form = FoodDonationForm()

    template_name = "public/partials/donation_form.html" if request.htmx else "public/donate_food.html"

    return render(request, template_name, {"form": form, "submitted": submitted})
