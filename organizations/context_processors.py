from django.http.request import HttpRequest


def current_organization(request: HttpRequest):
    return {
        "current_organization": request.organization,
    }
