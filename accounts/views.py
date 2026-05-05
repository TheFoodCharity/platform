from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.http.response import HttpResponseRedirect
from django.views.generic.edit import FormView

from .forms import RegistrationForm


class LoginView(BaseLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class RegistrationView(FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm
    success_url = "/"  # TODO(alex): redirect to email verification page

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
