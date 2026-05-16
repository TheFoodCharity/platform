from django.shortcuts import HttpResponse, render

from collaborations.models import CollaborationSpace
from donations.models import Donation
from organizations.models import Organization
from storage.models import StorageLocation


def home(request):
    return render(request, "public/landing.html")


def demo_interest(request):
    return HttpResponse(
        "Thanks! Demo requests are open - contact us to schedule one.",
    )


def dashboard(request):
    active_organizations_count = Organization.objects.filter(
        is_active=True,
    ).count()

    pending_donations_count = Donation.objects.filter(
        status__in=[
            Donation.Status.SUBMITTED,
            Donation.Status.PENDING,
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
