from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse


def _redirect_to_dispatch(request):
    return redirect_to_login(request.get_full_path(), reverse("organizations:dispatch"))


class OrganizationRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.organization.is_anonymous:
            return _redirect_to_dispatch(request)
        return super().dispatch(request, *args, **kwargs)


def organization_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.organization.is_anonymous:
            return _redirect_to_dispatch(request)
        return view_func(request, *args, **kwargs)

    return wrapper
