from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView
from django_htmx.http import HttpResponseClientRefresh

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


class DispatchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        match list(request.user.organizations.all()[:2]):
            case []:
                return redirect(reverse("organizations:apply"))
            case [organization]:
                set_current_organization(request, organization)
                # TODO(alex): redirect to that org's dashboard once it exists
                return redirect("/")
            case _:
                return redirect(reverse("organizations:select"))


class ApplyView(LoginRequiredMixin, FormView):
    template_name = "organizations/apply.html"
    form_class = ApplicationCreateForm

    def __init__(self):
        super().__init__()
        self.object = None

    def get_success_url(self):
        return reverse("organizations:application")

    def form_valid(self, form):
        self.object = organization_create(
            owner=self.request.user,
            name=form.cleaned_data["name"],
            organization_type=form.cleaned_data["organization_type"],
        )
        set_current_organization(self.request, self.object)
        return super().form_valid(form)


class ApplicationDashboardView(LoginRequiredMixin, SingleObjectMixin, FormView):
    template_name = "organizations/application/dashboard.html"
    model = Organization
    form_class = ApplicationSubmitForm

    def __init__(self):
        super().__init__()
        self.object = None

    def get_object(self, queryset=None):
        return self.request.organization

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
        return super().get_context_data(application=self.object.application, **kwargs)

    def form_valid(self, form):
        if not self.object.is_editable():
            raise PermissionDenied()
        self.object.application.submit(by=self.request.user)
        self.object.submit()
        return super().form_valid(form)


class ApplicationFormView(LoginRequiredMixin, UpdateView):
    template_name = "organizations/application/form.html"
    model = Organization
    section: str
    section_title: str

    def get_object(self, queryset=None):
        return self.request.organization

    def get_context_data(self, **kwargs):
        return super().get_context_data(section_title=self.section_title, **kwargs)

    def form_valid(self, form):
        if not self.object.is_editable():
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
        if (not request.htmx or request.htmx.boosted) and request.organization:
            return redirect("/")  # TODO(alex): redirect to dashboard
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
        try:
            if request.user.is_staff:
                organization = Organization.active.get(pk=pk)
            else:
                organization = Organization.active.for_user(request.user).get(pk=pk)
            set_current_organization(request, organization)
        except Organization.DoesNotExist:
            pass

        return HttpResponseClientRefresh()
