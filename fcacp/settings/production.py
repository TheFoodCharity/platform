from .base import *  # noqa: F403
from .env import ProductionEnvironment

env = ProductionEnvironment()

DEBUG = False

SECRET_KEY = env.secret_key.get_secret_value()

ALLOWED_HOSTS = env.allowed_hosts

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "pool": True,
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
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
} if env.aws_storage_bucket_name else {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": PRIVATE_MEDIA_ROOT,  # noqa: F405
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CELERY_BROKER_URL = str(env.broker_url)
CELERY_TASK_IGNORE_RESULT = True

CLAMAV_HOST = env.clamav.host
CLAMAV_PORT = env.clamav.port
CLAMAV_TIMEOUT = env.clamav.timeout

CRISPY_FAIL_SILENTLY = True

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
# Render.com terminates TLS at its edge and forwards requests over HTTP with
# X-Forwarded-Proto; this header must be trusted so SECURE_SSL_REDIRECT doesn't
# infinite-loop and request.is_secure() returns True correctly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
