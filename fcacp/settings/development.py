import secrets
import warnings

from .base import *  # noqa: F403
from .env import DevelopmentEnvironment

env = DevelopmentEnvironment()

DEBUG = True

if env.secret_key is not None:
    SECRET_KEY = env.secret_key.get_secret_value()
else:
    _key = "django-insecure-" + secrets.token_urlsafe(50)
    warnings.warn(
        f"SECRET_KEY is not set — using an ephemeral key. Sessions will be "
        f"invalidated on every restart. Add this to your .env:\n\n"
        f"    SECRET_KEY={_key}\n",
        stacklevel=1,
    )
    SECRET_KEY = _key

ALLOWED_HOSTS = env.allowed_hosts

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "pool": False,
            "server_side_binding": True,
        },
        **env.database_url.to_django(),
    }
}

EMAIL_HOST = env.smtp.host
EMAIL_PORT = env.smtp.port
EMAIL_HOST_USER = env.smtp.username
EMAIL_HOST_PASSWORD = env.smtp.password.get_secret_value()
EMAIL_USE_TLS = env.smtp.use_tls
EMAIL_USE_SSL = env.smtp.use_ssl
EMAIL_TIMEOUT = env.smtp.timeout

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env.aws_storage_bucket_name,
            "region_name": env.aws_s3_region_name or None,
            "access_key": env.aws_s3_access_key_id or None,
            "secret_key": env.aws_s3_secret_access_key or None,
            "default_acl": None,
            "querystring_auth": True,
            "file_overwrite": False,
        },
    },
} if env.aws_storage_bucket_name else {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": PRIVATE_MEDIA_ROOT,  # noqa: F405
        },
    },
}

CELERY_BROKER_URL = str(env.broker_url)
CELERY_TASK_IGNORE_RESULT = True

CLAMAV_HOST = env.clamav.host
CLAMAV_PORT = env.clamav.port
CLAMAV_TIMEOUT = env.clamav.timeout

# Serve static files via finders so collectstatic is not required for runserver
WHITENOISE_USE_FINDERS = True

CRISPY_FAIL_SILENTLY = False

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Edge additions only — see ordering contract in base.py
INSTALLED_APPS = [*INSTALLED_APPS, "django_browser_reload"]  # noqa: F405
MIDDLEWARE = [*MIDDLEWARE, "django_browser_reload.middleware.BrowserReloadMiddleware"]  # noqa: F405
