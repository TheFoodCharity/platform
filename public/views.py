from django.shortcuts import HttpResponse, render


def home(request):
    return render(request, "public/landing.html")


def dashboard(request):
    return render(request, "public/dashboard.html")


def food_help_map(request):
    return render(request, "public/food_help_map.html")


def demo_interest(request):
    return HttpResponse(
        "Thanks! Demo requests are open - contact us to schedule one."
    )