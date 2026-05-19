import secrets

from .base import *  # noqa: F403

# Build context: collectstatic and tailwind build only. No runtime config is
# present or required; SECRET_KEY is ephemeral and process-local since neither
# command signs any persistent data.
DEBUG = False
SECRET_KEY = secrets.token_urlsafe(50)
ALLOWED_HOSTS = []
DATABASES = {}

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
