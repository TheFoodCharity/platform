import os
from datetime import timedelta
from pathlib import Path

from django.contrib.messages import constants as message_constants

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INTERNAL_IPS = ["127.0.0.1", "::1"]

# Ordering contract: every ordering-sensitive app/middleware is defined here so
# adjacency requirements are statically visible in one place. Context modules
# (development, production, build) may only make edge additions using list
# rebinding — [*INSTALLED_APPS, "new.app"] or [*MIDDLEWARE, "new.Middleware"] —
# never mutate these lists and never insert at a hardcoded index.
#
# If a future context needs a mid-list insert, do it relative to a named anchor:
#   idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
#   MIDDLEWARE = [*MIDDLEWARE[:idx+1], "new.Middleware", *MIDDLEWARE[idx+1:]]
#
# Key constraints:
#   MIDDLEWARE: WhiteNoiseMiddleware must be directly after SecurityMiddleware;
#               DebugToolbarMiddleware must come before any response middleware
#   INSTALLED_APPS: whitenoise.runserver_nostatic must precede django.contrib.staticfiles
INSTALLED_APPS = [
    # 3rd-party
    "crispy_forms",
    "debug_toolbar",
    "django_htmx",
    "phonenumber_field",
    "rules.apps.AutodiscoverRulesConfig",
    "storages",
    "tailwind",
    "whitenoise.runserver_nostatic",
    # 1st-party
    "accounts",
    "collaborations",
    "forums",
    "organizations",
    "permissions",
    "public",
    "storage",
    "donations",
    "theme",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "organizations.middleware.CurrentOrganizationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "fcacp.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "organizations.context_processors.current_organization",
            ],
        },
    },
]

WSGI_APPLICATION = "fcacp.wsgi.application"

# Storage
# https://docs.djangoproject.com/en/6.0/ref/settings/#storages
COLLABORATION_FILE_UPLOAD_MAX_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 52 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/
USE_I18N = True
LANGUAGE_CODE = "en-us"

USE_TZ = True
TIME_ZONE = "UTC"

# Use E.123 format for extension support
# https://en.wikipedia.org/wiki/E.123#Telephone_number
PHONENUMBER_DEFAULT_FORMAT = "INTERNATIONAL"
PHONENUMBER_DB_FORMAT = "INTERNATIONAL"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "assets"

# Theming
TAILWIND_APP_NAME = "theme"

if os.name == "nt":
    NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"

CRISPY_ALLOWED_TEMPLATE_PACKS = ["fcacp"]
CRISPY_TEMPLATE_PACK = "fcacp"

MESSAGE_TAGS = {
    message_constants.DEBUG: "alert-debug",
    message_constants.INFO: "alert-info",
    message_constants.SUCCESS: "alert-success",
    message_constants.WARNING: "alert-warning",
    message_constants.ERROR: "alert-error",
}

# Authentication
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "rules.permissions.ObjectPermissionBackend",
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "organizations:dispatch"
LOGOUT_REDIRECT_URL = "accounts:login"

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # 1 day

INVITATION_TTL = timedelta(hours=72)

# Email
# https://docs.djangoproject.com/en/6.0/topics/email/
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@fcacp.local"

# Debugging
DEBUG_TOOLBAR_CONFIG = {"ROOT_TAG_EXTRA_ATTRS": "hx-preserve"}
