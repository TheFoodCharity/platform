from django.shortcuts import HttpResponse, render


def home(request):
    return render(request, "public/landing.html")

def demo_interest(request):
    return HttpResponse("Thanks! Demo requests are open - contact us to schedule one.")
