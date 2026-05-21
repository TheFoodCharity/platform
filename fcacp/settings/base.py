import os
from datetime import timedelta
from os import environ
from pathlib import Path

from django.contrib.messages import constants as message_constants

from .env import BaseEnvironment

BASE_DIR = Path(__file__).resolve().parent.parent.parent

_env = BaseEnvironment()

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
    "fcacp.middleware.HtmxMessagesMiddleware",
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

STORAGES = {
    "default": _env.storage.to_django(),
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

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
STATICFILES_DIRS = [BASE_DIR / "static"]

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

# Debugging
DEBUG_TOOLBAR_CONFIG = {"ROOT_TAG_EXTRA_ATTRS": "hx-preserve"}

ALLOWED_HOSTS = _env.allowed_hosts
if render_hostname := environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(render_hostname)

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "pool": False,
            "server_side_binding": True,
        },
        **_env.database_url.to_django(),
    }
}

# Email
# https://docs.djangoproject.com/en/6.0/topics/email/
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = _env.smtp.from_email

EMAIL_HOST = _env.smtp.host
EMAIL_PORT = _env.smtp.port
EMAIL_HOST_USER = _env.smtp.username
EMAIL_HOST_PASSWORD = _env.smtp.password.get_secret_value()
EMAIL_USE_TLS = _env.smtp.use_tls
EMAIL_USE_SSL = _env.smtp.use_ssl
EMAIL_TIMEOUT = _env.smtp.timeout

# Celery
# https://docs.celeryq.dev/en/stable/userguide/configuration.html
CELERY_BROKER_URL = str(_env.broker_url)
CELERY_TASK_IGNORE_RESULT = True

# ClamAV settings
CLAMAV_HOST = _env.clamav.host
CLAMAV_PORT = _env.clamav.port
CLAMAV_TIMEOUT = _env.clamav.timeout
