import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fcacp.settings.development")

app = Celery("fcacp")
app.config_from_object("django.conf:settings", namespace="CELERY")

if concurrency := os.environ.get("WORKER_CONCURRENCY"):
    app.conf.worker_concurrency = int(concurrency)

app.autodiscover_tasks()
