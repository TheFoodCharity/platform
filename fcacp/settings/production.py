from os import environ

from .base import *  # noqa: F403
from .env import ProductionEnvironment

_env = ProductionEnvironment()

DEBUG = False

SECRET_KEY = _env.secret_key.get_secret_value()

if internal_name := environ.get("RENDER_SERVICE_NAME"):
    ALLOWED_HOSTS.append(internal_name)  # noqa: F405

DATABASES["default"]["OPTIONS"]["pool"] = True  # noqa: F405

STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

CRISPY_FAIL_SILENTLY = True

CSRF_COOKIE_SECURE = _env.https
SESSION_COOKIE_SECURE = _env.https
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = _env.https
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
# Render.com terminates TLS at its edge and forwards requests over HTTP with
# X-Forwarded-Proto; this header must be trusted so SECURE_SSL_REDIRECT doesn't
# infinite-loop and request.is_secure() returns True correctly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if _env.https else None
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
