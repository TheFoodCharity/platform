from django.shortcuts import HttpResponse, render

from public.models import FoodHelpLocation


def home(request):
    return render(request, "public/landing.html")


def food_help_map(request):
    locations = FoodHelpLocation.objects.filter(
        is_public=True,
        is_approved=True,
    )

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
