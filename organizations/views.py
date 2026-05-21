from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh

from .decorators import OrganizationRequiredMixin
from .exceptions import InvitationAlreadyAccepted, InvitationEmailMismatch, InvitationError, InvitationExpired
from .forms import (
    ApplicationBasicDetailsForm,
    ApplicationContactForm,
    ApplicationCreateForm,
    ApplicationLocationForm,
    ApplicationOperationsForm,
    ApplicationSubmitForm,
    InvitationSendForm,
    MemberPermissionsForm,
    ProfileForm,
)
from .models import Invitation, Membership, Organization
from .services import (
    accept_invitation,
    decode_invitation_pk,
    invitation_accept_path,
    invitation_token_generator,
    organization_create,
    send_invitation_email,
    set_current_organization,
    update_member_permissions,
)

User = get_user_model()

PENDING_INVITATION_KEY = "organizations:pending_invitation"


def _safe_next(request, source):
    next_url = source.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return None


class DispatchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Finalize a pending invitation carried via session (register→verify→dispatch path).
        if pending_pk := request.session.pop(PENDING_INVITATION_KEY, None):
            try:
                invitation = Invitation.objects.select_related("organization").get(pk=pending_pk)
                accept_invitation(invitation=invitation, user=request.user)
                set_current_organization(request, invitation.organization)
                messages.success(request, f"Welcome! You've joined {invitation.organization}.")
                return redirect(reverse("dashboard"))
            except Invitation.DoesNotExist, InvitationExpired, InvitationAlreadyAccepted:
                pass
            except InvitationEmailMismatch:
                messages.warning(
                    request,
                    "The invitation could not be applied: your account email does not match the invited address.",
                )

        next_url = _safe_next(request, request.GET)
        match list(request.user.organizations.all()[:2]):
            case []:
                return redirect(reverse("organizations:apply"))
            case [organization]:
                set_current_organization(request, organization)
                return redirect(next_url or reverse_lazy("dashboard"))
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


class ApplicationDashboardView(OrganizationRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, FormView):
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


class ApplicationFormView(OrganizationRequiredMixin, PermissionRequiredMixin, UpdateView):
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
            return redirect(next_url or reverse_lazy("dashboard"))
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
            return HttpResponseClientRedirect(next_url or reverse_lazy("dashboard"))
        return HttpResponseClientRefresh()


class SettingsPageMixin(OrganizationRequiredMixin, PermissionRequiredMixin):
    section_id: str
    tab_id: str | None = None

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["section_id"] = self.section_id
        data["tab_id"] = self.tab_id or self.section_id
        return data


class ProfileView(SettingsPageMixin, UpdateView):
    template_name = "organizations/settings/profile.html"
    form_class = ProfileForm
    success_url = reverse_lazy("organizations:profile")
    context_object_name = "organization"

    section_id = "profile"

    permission_required = "organizations.view_profile"

    def get_object(self, queryset=None):
        return self.request.organization

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["editable"] = self.request.user.has_perm("organizations.edit_profile")
        return kwargs

    def form_valid(self, form):
        if not self.request.user.has_perm("organizations.edit_profile"):
            raise PermissionDenied()

        response = super().form_valid(form)
        messages.success(self.request, "Profile successfully updated")
        return response


class MembersView(SettingsPageMixin, ListView):
    template_name = "organizations/settings/members_list.html"
    model = Membership
    context_object_name = "members"

    section_id = "members"

    permission_required = "organizations.view_members"

    def get_queryset(self):
        return Membership.objects.filter(organization=self.request.organization)


class MemberDetailView(SettingsPageMixin, UpdateView):
    template_name = "organizations/settings/members_detail.html"
    model = Membership
    context_object_name = "member"
    form_class = MemberPermissionsForm

    section_id = "members-detail"
    tab_id = "members"

    permission_required = "organizations.view_members"

    def get_queryset(self):
        return Membership.objects.filter(organization=self.request.organization).select_related("user", "role")

    def get_object(self, queryset=None):
        if not hasattr(self, "_object_cache"):
            self._object_cache = super().get_object(queryset)
        return self._object_cache

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        kwargs["membership"] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs["can_edit_permissions"] = self.request.user.has_perm("organizations.edit_member_permissions")
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse("organizations:member", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        if not self.request.user.has_perm("organizations.edit_member_permissions"):
            raise PermissionDenied()
        update_member_permissions(
            membership=self.object,
            role=form.cleaned_data["role"],
            actions=form.actions(),
        )
        messages.success(self.request, "Member permissions updated")
        return redirect(self.get_success_url())


class MemberRemoveView(OrganizationRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "organizations.remove_member"

    def post(self, request, *args, pk, **kwargs):
        Membership.objects.filter(organization=request.organization, pk=pk).delete()
        messages.success(request, "The member was successfully removed from your organization!")
        return HttpResponseClientRedirect(reverse("organizations:members"))


class InvitationsView(SettingsPageMixin, ListView):
    template_name = "organizations/settings/invitations_list.html"
    model = Invitation
    context_object_name = "invitations"

    section_id = "invitations"

    permission_required = "organizations.invite_member"

    def get_queryset(self):
        return Invitation.objects.filter(organization=self.request.organization, accepted_at__isnull=True)


class InvitationsSendView(SettingsPageMixin, CreateView):
    template_name = "organizations/settings/invitations_create.html"
    model = Invitation
    context_object_name = "invitation"
    form_class = InvitationSendForm
    success_url = reverse_lazy("organizations:invitations")

    section_id = "invitations-create"
    tab_id = "invitations"

    permission_required = "organizations.invite_member"

    def get_template_names(self):
        names = super().get_template_names()
        if self.request.htmx and not self.request.htmx.boosted:
            return [f"{name}#form" for name in names]

        return names

    def get_success_url(self):
        return self.success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["invited_by"] = self.request.user
        kwargs["organization"] = self.request.organization
        return kwargs

    def form_valid(self, form):
        super().form_valid(form)
        send_invitation_email(self.object, self.request)
        return HttpResponseClientRedirect(self.get_success_url())


class InvitationAcceptView(SingleObjectMixin, TemplateResponseMixin, View):
    template_name = "organizations/invitation_accept.html"
    context_object_name = "invitation"

    def get_queryset(self):
        return Invitation.objects.select_related("organization", "invited_by")

    def get_object(self, queryset=None):
        if hasattr(self, "_object_cache"):
            return self._object_cache
        pk = decode_invitation_pk(self.kwargs["invb64"])
        try:
            inv = (queryset or self.get_queryset()).get(pk=pk) if pk is not None else None
        except Invitation.DoesNotExist:
            inv = None
        if inv is not None and not (
            invitation_token_generator.check_token(inv, self.kwargs["token"])
            and inv.accepted_at is None
            and timezone.now() <= inv.expires_at
        ):
            inv = None
        self._object_cache = inv
        return self._object_cache

    def get_context_data(self, **kwargs):
        invitation = self.object
        if invitation is None:
            return {"state": "invalid"}
        if self.request.user.email.lower() != invitation.email.lower():
            accept_url = self.request.build_absolute_uri(invitation_accept_path(invitation))
            return {
                "state": "mismatch",
                "invitation": invitation,
                "logout_url": f"{reverse('accounts:logout')}?{urlencode({'next': accept_url})}",
            }
        return {"state": "confirm", "invitation": invitation}

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get(self, request, *args, **kwargs):
        if self.object is not None and not request.user.is_authenticated:
            request.session[PENDING_INVITATION_KEY] = self.object.pk
            accept_url = request.build_absolute_uri(invitation_accept_path(self.object))
            if User.objects.filter(email__iexact=self.object.email).exists():
                return redirect(f"{reverse('accounts:login')}?{urlencode({'next': accept_url})}")
            return redirect(reverse("accounts:register"))

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("accounts:login"))

        invitation = self.object

        if invitation is None or request.user.email.lower() != invitation.email.lower():
            return self.render_to_response(self.get_context_data())

        try:
            accept_invitation(invitation=invitation, user=request.user)
        except InvitationError:
            self.object = None  # render "invalid" for any race/error
            return self.render_to_response(self.get_context_data())

        set_current_organization(request, invitation.organization)
        messages.success(request, f"Welcome! You've joined {invitation.organization}.")
        return redirect(reverse("dashboard"))


class InvitationRemoveView(OrganizationRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "organizations.invite_member"

    def post(self, request, *args, pk, **kwargs):
        Invitation.objects.filter(organization=request.organization, pk=pk).delete()
        messages.success(request, "The invitation was successfully rescinded!")
        return HttpResponseClientRefresh()
