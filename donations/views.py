from django.shortcuts import get_object_or_404, redirect, render

from storage.models import StorageLocation

from .forms import DonationTicketForm
from .models import DonationTicket


def donation_ticket_list(request):
    tickets = DonationTicket.objects.all().order_by("-created_at")

    status = request.GET.get("status")
    storage_requirement = request.GET.get("storage_requirement")

    if status:
        tickets = tickets.filter(status=status)

    if storage_requirement:
        tickets = tickets.filter(storage_requirement=storage_requirement)

    context = {
        "tickets": tickets,
        "status_choices": DonationTicket.Status.choices,
        "storage_requirement_choices": DonationTicket.StorageRequirement.choices,
    }

    return render(request, "donations/donation_ticket_list.html", context)


def donation_ticket_create(request):
    if request.method == "POST":
        form = DonationTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.status = DonationTicket.Status.SUBMITTED
            ticket.save()
            return redirect("donations:detail", pk=ticket.pk)
    else:
        form = DonationTicketForm()

    return render(
        request,
        "donations/donation_ticket_form.html",
        {"form": form, "title": "Create Donation Ticket"},
    )


def donation_ticket_edit(request, pk):
    ticket = get_object_or_404(DonationTicket, pk=pk)

    if request.method == "POST":
        form = DonationTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save()
            return redirect("donations:detail", pk=ticket.pk)
    else:
        form = DonationTicketForm(instance=ticket)

    return render(
        request,
        "donations/donation_ticket_form.html",
        {"form": form, "title": "Edit Donation Ticket"},
    )


def donation_ticket_detail(request, pk):
    ticket = get_object_or_404(DonationTicket, pk=pk)

    matching_storage = StorageLocation.objects.filter(
        is_active=True,
        approval_status=StorageLocation.ApprovalStatus.APPROVED,
        capacity_status=StorageLocation.CapacityStatus.AVAILABLE,
    )

    if ticket.storage_requirement != DonationTicket.StorageRequirement.NONE:
        matching_storage = matching_storage.filter(
            storage_type=ticket.storage_requirement,
        )

    matching_storage = matching_storage.filter(
        available_space__gte=ticket.quantity,
    )

    return render(
        request,
        "donations/donation_ticket_detail.html",
        {
            "ticket": ticket,
            "matching_storage": matching_storage,
        },
    )


def donation_ticket_assign_storage(request, pk, storage_pk):
    ticket = get_object_or_404(DonationTicket, pk=pk)
    storage_location = get_object_or_404(StorageLocation, pk=storage_pk)

    ticket.assign_storage(storage_location)

    return redirect("donations:detail", pk=ticket.pk)
