from django.contrib import messages
from django.shortcuts import HttpResponse, redirect, render

from collaborations.models import CollaborationSpace
from donations.models import Donation
from organizations.decorators import organization_required
from organizations.models import Organization
from storage.models import StorageLocation


def healthcheck(request):
    return HttpResponse(status=204)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "public/landing.html")


def food_help_map(request):
    locations = Organization.objects.filter(
        is_active=True,
        is_publicly_visible=True,
        status__in=[
            Organization.Status.APPROVED,
            Organization.Status.APPROVED_LIMITED,
        ],
    ).order_by("municipality", "name")

    municipality = request.GET.get("municipality")

    if municipality:
        locations = locations.filter(
            municipality__icontains=municipality,
        )

    return render(
        request,
        "public/food_help_map.html",
        {
            "locations": locations,
            "municipality": municipality or "",
        },
    )


def demo_interest(request):
    return HttpResponse(
        "Thanks! Demo requests are open - contact us to schedule one.",
    )


def custom_404_view(request, exception=None):
    messages.error(request, "The page you're looking for doesn't exist!")
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("home")


@organization_required
def dashboard(request):
    active_organizations_count = Organization.objects.filter(
        is_active=True,
    ).count()

    pending_donations_count = Donation.objects.filter(
        status__in=[
            Donation.Status.SUBMITTED,
            Donation.Status.AVAILABLE,
        ],
    ).count()

    available_storage_count = StorageLocation.objects.filter(
        is_active=True,
        capacity_status=StorageLocation.CapacityStatus.AVAILABLE,
    ).count()

    active_collaborations_count = CollaborationSpace.objects.filter(
        status=CollaborationSpace.Status.ACTIVE,
    ).count()

    recent_donations = Donation.objects.order_by(
        "-created_at",
    )[:5]

    return render(
        request,
        "public/dashboard.html",
        {
            "active_organizations_count": active_organizations_count,
            "pending_donations_count": pending_donations_count,
            "available_storage_count": available_storage_count,
            "active_collaborations_count": active_collaborations_count,
            "recent_donations": recent_donations,
        },
    )
