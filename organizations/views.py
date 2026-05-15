from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from rules.contrib.views import PermissionRequiredMixin

from .decorators import OrganizationRequiredMixin
from .forms import (
    ApplicationBasicDetailsForm,
    ApplicationContactForm,
    ApplicationCreateForm,
    ApplicationLocationForm,
    ApplicationOperationsForm,
    ApplicationSubmitForm,
)
from .models import Organization
from .services import organization_create, set_current_organization


def _safe_next(request, source):
    next_url = source.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return None


class OrganizationPermissionMixin(PermissionRequiredMixin):
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.organization:
            return redirect(reverse("organizations:dispatch"))
        return super().handle_no_permission()


class DispatchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        next_url = _safe_next(request, request.GET)
        match list(request.user.organizations.all()[:2]):
            case []:
                return redirect(reverse("organizations:apply"))
            case [organization]:
                set_current_organization(request, organization)
                # TODO(alex): redirect to that org's dashboard once it exists
                return redirect(next_url or "/")
            case _:
                select_url = reverse("organizations:select")
                if next_url:
                    select_url = f"{select_url}?{urlencode({'next': next_url})}"
                return redirect(select_url)


class ApplyView(LoginRequiredMixin, FormView):
    template_name = "organizations/apply.html"
    form_class = ApplicationCreateForm

    def get_success_url(self):
        return reverse("organizations:application")

    def form_valid(self, form):
        organization = organization_create(
            owner=self.request.user,
            name=form.cleaned_data["name"],
            organization_type=form.cleaned_data["organization_type"],
        )
        set_current_organization(self.request, organization)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["organization_count"] = Organization.objects.for_user(self.request.user).count()
        return data


class ApplicationDashboardView(OrganizationRequiredMixin, SingleObjectMixin, FormView):
    template_name = "organizations/application/dashboard.html"
    model = Organization
    form_class = ApplicationSubmitForm
    permission_required = "organizations.view_application"

    def __init__(self):
        super().__init__()
        self.object = None

    def get_object(self, queryset=None):
        organization = self.request.organization
        if organization.is_anonymous:
            raise Http404("No organization found")
        return organization

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("organizations:application")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization_status"] = self.object.status
        return kwargs

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            application=self.object.application,
            show_edit=self.object.is_editable() and self.request.user.has_perm("organizations.edit_application"),
            **kwargs,
        )

    def form_valid(self, form):
        if not self.request.user.has_perm("organizations.submit_application"):
            raise PermissionDenied()
        self.object.application.submit(by=self.request.user)
        self.object.submit()
        return super().form_valid(form)


class ApplicationFormView(OrganizationRequiredMixin, UpdateView):
    template_name = "organizations/application/form.html"
    model = Organization
    section: str
    section_title: str
    permission_required = "organizations.view_application"

    def get_object(self, queryset=None):
        return self.request.organization

    def get_context_data(self, **kwargs):
        return super().get_context_data(section_title=self.section_title, **kwargs)

    def form_valid(self, form):
        if not self.request.user.has_perm("organizations.edit_application"):
            raise PermissionDenied()

        response = super().form_valid(form)
        self.object.application.mark_section_updated(self.section)
        return response

    def get_success_url(self):
        return reverse("organizations:application")


class ApplicationBasicDetailsView(ApplicationFormView):
    form_class = ApplicationBasicDetailsForm
    section = "basics"
    section_title = "Basic information"


class ApplicationLocationView(ApplicationFormView):
    form_class = ApplicationLocationForm
    section = "location"
    section_title = "Location & service area"


class ApplicationContactView(ApplicationFormView):
    form_class = ApplicationContactForm
    section = "contact"
    section_title = "Contact details"


class ApplicationOperationsView(ApplicationFormView):
    form_class = ApplicationOperationsForm
    section = "operations"
    section_title = "Interests & preferences"


class SelectView(LoginRequiredMixin, ListView):
    template_name = "organizations/select.html"
    context_object_name = "organizations"

    def get(self, request, *args, **kwargs):
        if (not request.htmx or request.htmx.boosted) and not request.organization.is_anonymous:
            next_url = _safe_next(request, request.GET)
            return redirect(next_url or "/")  # TODO(alex): redirect to dashboard
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Organization.objects.all()
        return Organization.objects.for_user(self.request.user)

    def get_template_names(self):
        names = super().get_template_names()
        if self.request.htmx and not self.request.htmx.boosted:
            return [f"{name}#options" for name in names]

        return names


class ActivateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        was_anonymous = request.organization.is_anonymous
        try:
            qs = Organization.objects if request.user.is_staff else Organization.objects.for_user(request.user)
            organization = qs.get(pk=pk)
            set_current_organization(request, organization)
        except Organization.DoesNotExist:
            return HttpResponseClientRefresh()

        if was_anonymous:
            next_url = _safe_next(request, request.POST)
            return HttpResponseClientRedirect(next_url or "/")
        return HttpResponseClientRefresh()
