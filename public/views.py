from django.shortcuts import HttpResponse, render

from organizations.models import Organization


def home(request):
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