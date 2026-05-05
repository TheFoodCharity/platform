from django.db import transaction
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.views.generic.base import TemplateView

from .forms import UserRegistrationForm


class ApplyView(TemplateView):
    template_name = "accounts/apply.html"
    success_url = "/"  # TODO(alex): switch to pending page

    def get_context_data(self, **kwargs):
        kwargs.setdefault("user_form", UserRegistrationForm(prefix="user"))
        # kwargs.setdefault("organization_form", OrganizationRegistrationForm(prefix="org"))
        return super().get_context_data(**kwargs)

    def post(self, request: HttpRequest, *args, **kwargs):
        user_form = UserRegistrationForm(request.POST, prefix="user")
        # organization_form = OrganizationRegistrationForm(request.POST, prefix="org")

        # if not (user_form.is_valid() and organization_form.is_valid()):
        if not user_form.is_valid():
            return self.render_to_response(
                self.get_context_data(user_form=user_form)  # , organization_form=organization_form)
            )

        with transaction.atomic():
            _user = user_form.save()
            # Organization.create(name=organization_form.cleaned_data["name"], owner=user)

        return redirect(self.success_url)
