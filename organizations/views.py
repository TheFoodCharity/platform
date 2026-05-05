from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View


class DispatchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        match request.user.organizations.count():
            case 0:
                return redirect(reverse("organizations:apply"))
            case 1:
                # TODO(alex): redirect to that org's dashboard once it exists
                return redirect("/")
            case _:
                return redirect(reverse("organizations:select"))
