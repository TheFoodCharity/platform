import secrets
import warnings

from .base import *  # noqa: F403
from .env import DevelopmentEnvironment

_env = DevelopmentEnvironment()

DEBUG = True

if _env.secret_key is not None:
    SECRET_KEY = _env.secret_key.get_secret_value()
else:
    _key = "django-insecure-" + secrets.token_urlsafe(50)
    warnings.warn(
        f"SECRET_KEY is not set — using an ephemeral key. Sessions will be "
        f"invalidated on every restart. Add this to your .env:\n\n"
        f"    SECRET_KEY={_key}\n",
        stacklevel=1,
    )
    SECRET_KEY = _key

# Serve static files via finders so collectstatic is not required for runserver
WHITENOISE_USE_FINDERS = True

CRISPY_FAIL_SILENTLY = False

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Edge additions only — see ordering contract in base.py
INSTALLED_APPS = [*INSTALLED_APPS, "django_browser_reload"]  # noqa: F405
MIDDLEWARE = [*MIDDLEWARE, "django_browser_reload.middleware.BrowserReloadMiddleware"]  # noqa: F405
