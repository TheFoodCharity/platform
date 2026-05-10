from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView

from .exceptions import VerificationExpired, VerificationInvalid, VerificationLocked
from .forms import LoginForm, RegistrationForm, VerificationForm
from .models import User, VerificationCode

PENDING_VERIFY_USER_KEY = "accounts:pending_verify_user_id"


class LoginView(BaseLoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.email_verified:
            user.send_verification_email(self.request)
            self.request.session[PENDING_VERIFY_USER_KEY] = user.pk
            messages.info(self.request, f"We sent a verification code to {user.email}.")
            return redirect("accounts:verify")

        return super().form_valid(form)


class RegistrationView(FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("accounts:verify")

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        user.send_verification_email(self.request)
        self.request.session[PENDING_VERIFY_USER_KEY] = user.pk
        messages.info(self.request, f"We sent a verification code to {user.email}.")
        return super().form_valid(form)


class EmailUnverifiedMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        if not ("token" in request.GET or "token" in request.POST or PENDING_VERIFY_USER_KEY in request.session):
            return redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def resolve_user(self, token: str | None = None) -> User | None:
        if token:
            return User.for_token(token)

        if pk := self.request.session.get(PENDING_VERIFY_USER_KEY):
            try:
                return User.objects.get(pk=pk)
            except User.DoesNotExist:
                self.request.session.pop(PENDING_VERIFY_USER_KEY)
                pass

        return None


class VerifyView(EmailUnverifiedMixin, FormView):
    template_name = "accounts/verify.html"
    form_class = VerificationForm
    success_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)

    def get_initial(self):
        initial = super().get_initial()

        if code := self.request.GET.get("code", "").strip().upper():
            initial["code"] = code
        if token := self.request.GET.get("token", "").strip():
            initial["token"] = token

        return initial

    def form_valid(self, form):
        user = self.resolve_user(token=form.cleaned_data["token"])
        if user is None:
            return self.form_invalid(form)

        try:
            VerificationCode.verify(
                user,
                VerificationCode.Purpose.EMAIL_VERIFICATION,
                form.cleaned_data["code"],
            )
        except VerificationExpired:
            form.add_error("code", "This code has expired. Request a new one below.")
            return self.form_invalid(form)
        except VerificationLocked:
            form.add_error("code", "Too many incorrect attempts. Request a new code below.")
            return self.form_invalid(form)
        except VerificationInvalid:
            form.add_error("code", "Invalid code. Please try again.")
            return self.form_invalid(form)

        self.request.session.pop(PENDING_VERIFY_USER_KEY, None)

        user.mark_email_verified()
        messages.success(self.request, "Your email has been verified.")
        login(self.request, user)
        return super().form_valid(form)


class ResendVerificationView(EmailUnverifiedMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):
        user = self.resolve_user(token=request.POST.get("token", None))
        if user is not None:
            user.send_verification_email(request)
            messages.info(request, f"A new verification code has been sent to {user.email}.")

        return HttpResponseRedirect(reverse_lazy("accounts:verify"))
