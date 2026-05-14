from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.utils.functional import SimpleLazyObject

from . import services


def get_current_organization(request: HttpRequest):
    if not hasattr(request, "_cached_organization"):
        request._cached_organization = services.get_current_organization(request)
    return request._cached_organization


class CurrentOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "session"):
            raise ImproperlyConfigured("The organization middleware requires session middleware to be installed")
        elif not hasattr(request, "user"):
            raise ImproperlyConfigured("The organization middleware requires authentication middleware to be installed")

        request.organization = SimpleLazyObject(lambda: get_current_organization(request))
        return self.get_response(request)
