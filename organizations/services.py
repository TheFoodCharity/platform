from contextlib import contextmanager
from typing import Iterable

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes
from django.utils.http import base36_to_int, urlsafe_base64_decode, urlsafe_base64_encode

from permissions import Scope, SystemCapability, SystemRole
from permissions.models import MembershipPermissionOverride, Permission, PermissionGroup

from .exceptions import InvitationAlreadyAccepted, InvitationEmailMismatch, InvitationExpired
from .models import (
    AnonymousOrganization,
    Invitation,
    Membership,
    Organization,
    OrganizationApplication,
    OrganizationType,
)

SESSION_KEY = "_organizations_current_id"

User = get_user_model()


# ---------------------------------------------------------------------------
# Invitation tokens
# ---------------------------------------------------------------------------


class InvitationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, invitation, timestamp):
        # Include accepted_at so the token self-invalidates when the invitation is
        # accepted — the same mechanism by which password-reset tokens self-invalidate
        # after a password change (that field is included in their hash value).
        return f"{invitation.pk}{invitation.accepted_at}{invitation.email}{timestamp}"

    def check_token(self, invitation, token):
        # Verify the HMAC only; time validity is enforced by Invitation.expires_at in the
        # view, so we intentionally skip the PASSWORD_RESET_TIMEOUT age check here.
        if not (invitation and token):
            return False
        try:
            ts_b36, _ = token.split("-", 1)
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False
        return constant_time_compare(self._make_token_with_timestamp(invitation, ts, self.secret), token)


invitation_token_generator = InvitationTokenGenerator()


def encode_invitation(invitation) -> str:
    return urlsafe_base64_encode(force_bytes(invitation.pk))


def decode_invitation_pk(invb64: str) -> int | None:
    try:
        return int(urlsafe_base64_decode(invb64).decode())
    except Exception:
        return None


def invitation_accept_path(invitation: Invitation) -> str:
    invb64 = encode_invitation(invitation)
    token = invitation_token_generator.make_token(invitation)
    return reverse("organizations:invitation_accept", args=[invb64, token])


# ---------------------------------------------------------------------------
# Invitation operations
# ---------------------------------------------------------------------------


def send_invitation_email(invitation: Invitation, request: HttpRequest):
    join_url = request.build_absolute_uri(invitation_accept_path(invitation))
    context = {
        "organization": invitation.organization,
        "invited_by": invitation.invited_by,
        "join_url": join_url,
        "expires_at": invitation.expires_at,
    }

    subject = loader.render_to_string("email/invitation_subject.txt", context)
    subject = "".join(subject.splitlines())  # Email subject cannot contain newlines

    html_body = loader.render_to_string("email/invitation.html", context)
    plain_body = loader.render_to_string("email/invitation.txt", context)

    message = EmailMultiAlternatives(subject, body=plain_body, to=[invitation.email])
    message.attach_alternative(html_body, "text/html")

    message.send()


@transaction.atomic()
def accept_invitation(*, invitation: Invitation, user) -> Membership:
    if invitation.accepted_at is not None:
        raise InvitationAlreadyAccepted
    if timezone.now() > invitation.expires_at:
        raise InvitationExpired
    if invitation.email.lower() != user.email.lower():
        raise InvitationEmailMismatch

    membership, _ = Membership.objects.get_or_create(
        user=user,
        organization=invitation.organization,
        defaults={"role": invitation.role},
    )
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at", "modified"])
    return membership


# ---------------------------------------------------------------------------
# Organization operations
# ---------------------------------------------------------------------------


@transaction.atomic()
def organization_create(*, owner: User, name: str, organization_type: OrganizationType) -> Organization:
    manager_role = PermissionGroup.objects.get(name=SystemRole.ORGANIZATION_MANAGER, scope=Scope.USER)
    default_capability = PermissionGroup.objects.get(name=SystemCapability.DEFAULT, scope=Scope.ORGANIZATION)

    organization = Organization.objects.create(owner=owner, name=name, organization_type=organization_type)
    organization.capabilities.add(default_capability)

    Membership.objects.create(user=owner, organization=organization, role=manager_role)
    OrganizationApplication.objects.create(organization=organization)
    return organization


@transaction.atomic()
def update_member_permissions(
    *,
    membership: Membership,
    role: PermissionGroup | None,
    actions: Iterable[tuple[str, str, int | None]],
) -> None:
    actions = list(actions)

    membership.role = role
    membership.permission_version = F("permission_version") + 1
    membership.save(update_fields=["role", "permission_version", "modified"])

    codes = [code for _action, code, _effect in actions]
    permissions_by_code = {p.code: p for p in Permission.objects.filter(code__in=codes)}

    remove_codes = [c for a, c, _ in actions if a == "remove"]
    if remove_codes:
        MembershipPermissionOverride.objects.filter(membership=membership, permission__code__in=remove_codes).delete()

    for action, code, effect in actions:
        if action == "remove":
            continue
        permission = permissions_by_code.get(code)
        if permission is None:
            continue
        MembershipPermissionOverride.objects.update_or_create(
            membership=membership,
            permission=permission,
            defaults={"effect": effect},
        )


# ---------------------------------------------------------------------------
# Session / organization context
# ---------------------------------------------------------------------------


def set_current_organization(request: HttpRequest, organization: Organization):
    if not request.user.is_authenticated:
        return
    if not (request.user.is_staff or organization.is_member(request.user)):
        return

    request.session[SESSION_KEY] = organization.pk
    request.session.cycle_key()


def get_current_organization(request: HttpRequest) -> Organization | AnonymousOrganization:
    if not request.user.is_authenticated:
        return AnonymousOrganization()

    try:
        pk = request.session[SESSION_KEY]
        if request.user.is_staff:
            return Organization.objects.get(pk=pk)
        return Organization.objects.for_user(request.user).get(pk=pk)
    except KeyError, Organization.DoesNotExist:
        pass

    return AnonymousOrganization()


@contextmanager
def acting_as(user: User, organization: Organization):
    """Pin the acting organization on ``user`` for the duration of the block.

    Restores the previous value on exit, including on exception and when nested.
    Handles the case where ``current_organization`` was not set beforehand.

    Use this in signals, management commands, and Celery tasks that need to perform
    a permission check outside of a request. Routes through the same predicates as views.
    """
    sentinel = object()
    previous = getattr(user, "current_organization", sentinel)
    user.current_organization = organization
    try:
        yield
    finally:
        if previous is sentinel:
            try:
                del user.current_organization
            except AttributeError:
                pass
        else:
            user.current_organization = previous
