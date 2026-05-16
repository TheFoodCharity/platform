import secrets
from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.core.signing import BadSignature, TimestampSigner
from django.db import models, transaction
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

VERIFICATION_TOKEN_SALT = "email-verification.v1"
VERIFICATION_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_TTL = timedelta(minutes=15)
VERIFICATION_MAX_ATTEMPTS = 5


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user: User = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)

    email_verified = models.BooleanField(
        _("email verified"),
        default=False,
        help_text=_("Designates whether this user's email has been verified as active."),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def send_verification_email(self, request) -> None:
        token = TimestampSigner(salt=VERIFICATION_TOKEN_SALT).sign(self.pk)
        _instance, code = VerificationCode.issue(
            self,
            VerificationCode.Purpose.EMAIL_VERIFICATION,
            ttl=VERIFICATION_TTL,
        )

        verify_url_base = reverse("accounts:verify")
        verify_url = request.build_absolute_uri(f"{verify_url_base}?code={code}&token={token}")

        context = {
            "user": self,
            "code": code,
            "verify_url": verify_url,
            "expires_minutes": int(VERIFICATION_TTL.total_seconds() // 60),
        }
        plain = get_template("email/verification.txt")
        html = get_template("email/verification.html")
        self.email_user(
            subject=_("Verify your email"),
            message=plain.render(context),
            html_message=html.render(context),
        )

    def mark_email_verified(self) -> None:
        self.email_verified = True
        self.save(update_fields=["email_verified"])

    @classmethod
    def for_token(cls, token: str):
        try:
            pk = TimestampSigner(salt=VERIFICATION_TOKEN_SALT).unsign(token, max_age=VERIFICATION_TTL)
            return cls.objects.get(pk=pk)
        except BadSignature, cls.DoesNotExist:
            return None


class VerificationCode(models.Model):
    class Purpose(models.IntegerChoices):
        EMAIL_VERIFICATION = 1, "Email verification"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verification_codes")
    purpose = models.PositiveSmallIntegerField(choices=Purpose.choices)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    remaining_attempts = models.PositiveSmallIntegerField(default=VERIFICATION_MAX_ATTEMPTS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "purpose"],
                name="unique_active_code_per_user_purpose",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_purpose_display()} for {self.user} (expires {self.expires_at:%Y-%m-%d %H:%M} UTC)"

    @classmethod
    def issue(
        cls,
        user: User,
        purpose: "VerificationCode.Purpose",
        *,
        ttl: timedelta,
        max_attempts: int = VERIFICATION_MAX_ATTEMPTS,
    ) -> tuple["VerificationCode", str]:
        plaintext = "".join(secrets.choice(VERIFICATION_CODE_ALPHABET) for _ in range(VERIFICATION_CODE_LENGTH))

        with transaction.atomic():
            cls.objects.filter(user=user, purpose=purpose).delete()
            instance = cls.objects.create(
                user=user,
                purpose=purpose,
                code_hash=make_password(plaintext),
                expires_at=timezone.now() + ttl,
                remaining_attempts=max_attempts,
            )
        return instance, plaintext

    @classmethod
    def verify(cls, user: User, purpose: "VerificationCode.Purpose", code: str) -> None:
        from .exceptions import VerificationExpired, VerificationInvalid, VerificationLocked

        code = code.strip().upper()
        try:
            instance = cls.objects.get(user=user, purpose=purpose)
        except cls.DoesNotExist:
            raise VerificationInvalid

        if timezone.now() > instance.expires_at:
            raise VerificationExpired

        if instance.remaining_attempts == 0:
            raise VerificationLocked

        instance.remaining_attempts -= 1
        instance.save(update_fields=["remaining_attempts"])

        if not check_password(code, instance.code_hash):
            raise VerificationInvalid

        instance.delete()
