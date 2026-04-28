import multiprocessing
from os import environ

host = environ.get("GUNICORN_HOST", "0.0.0.0")
port = environ.get("GUNICORN_PORT", "8000")

bind = f"{host}:{port}"
workers = multiprocessing.cpu_count() * 2 + 1

loglevel = environ.get("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
