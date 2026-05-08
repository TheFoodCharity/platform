from django.shortcuts import get_object_or_404, redirect, render

from donations.models import DonationTicket

from .forms import FoodRequestForm


def receiver_donation_list(request):
    tickets = DonationTicket.objects.exclude(
        status__in=[
            DonationTicket.Status.DRAFT,
            DonationTicket.Status.CANCELLED,
            DonationTicket.Status.EXPIRED,
            DonationTicket.Status.COMPLETED,
        ],
    ).order_by("-created_at")

    return render(request, "receivers/donation_list.html", {"tickets": tickets})


def receiver_donation_detail(request, pk):
    ticket = get_object_or_404(DonationTicket, pk=pk)

    return render(request, "receivers/donation_detail.html", {"ticket": ticket})


def food_request_create(request, pk):
    ticket = get_object_or_404(DonationTicket, pk=pk)

    if request.method == "POST":
        form = FoodRequestForm(request.POST)
        if form.is_valid():
            food_request = form.save(commit=False)
            food_request.donation_ticket = ticket
            food_request.save()
            return redirect("receivers:request_thanks", pk=food_request.pk)
    else:
        form = FoodRequestForm()

    return render(request, "receivers/food_request_form.html", {"form": form, "ticket": ticket})


def food_request_thanks(request, pk):
    return render(request, "receivers/food_request_thanks.html", {"request_id": pk})
