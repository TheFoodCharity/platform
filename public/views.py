from django.shortcuts import HttpResponse, render

from public.forms import FoodDonationForm
from public.models import FoodDonation


def home(request):
    return render(request, "public/landing.html")


def donate_food(request):
    form = FoodDonationForm(request.POST if request.method == "POST" else None)
    submitted = False

    if request.method == "POST" and form.is_valid():
        FoodDonation.objects.create(**form.cleaned_data)
        submitted = True
        form = FoodDonationForm()

    template_name = "public/partials/donation_form.html" if request.htmx else "public/donate_food.html"

    return render(request, template_name, {"form": form, "submitted": submitted})


def demo_interest(request):
    return HttpResponse("Thanks! Demo requests are open - contact us to schedule one.")
