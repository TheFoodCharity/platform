# Deployment

## Overview

The app is packaged as a Docker image. The build stage compiles Tailwind CSS and
collects static files; the runtime stage runs Gunicorn under a non-root user. All
runtime configuration is supplied via environment variables — there are no config
files to edit between environments.

The production settings module is `fcacp.settings.production` (set via
`DJANGO_SETTINGS_MODULE`, already baked into the image). It requires PostgreSQL
and an SMTP relay; there is no in-process fallback for either.

---

## Environment variables

All variables are read from the process environment (or a `.env` file when
running locally). See `.env.example` for a reference.

| Variable         | Required | Description                                                                               |
|------------------|----------|-------------------------------------------------------------------------------------------|
| `SECRET_KEY`     | Yes      | Django secret key — must be long, random, and kept secret                                 |
| `ALLOWED_HOSTS`  | Yes      | Comma-separated list of hostnames the app will serve (e.g. `example.com,www.example.com`) |
| `DATABASE_URL`   | Yes      | PostgreSQL DSN: `postgresql://user:password@host:5432/dbname`                             |
| `SMTP__HOST`     | No       | SMTP server hostname (default: `127.0.0.1`)                                               |
| `SMTP__PORT`     | No       | SMTP server port (default: `1025`)                                                        |
| `SMTP__USERNAME` | No       | SMTP authentication username                                                              |
| `SMTP__PASSWORD` | No       | SMTP authentication password                                                              |
| `SMTP__SECURITY` | No       | Connection security: `smtps`, `starttls`, or `none` (default: `none`)                     |
| `SMTP__TIMEOUT`  | No       | Connection timeout in seconds (default: none)                                             |

Generate a suitable `SECRET_KEY` with:

```sh
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Running the container

```sh
docker run \
  --env SECRET_KEY=... \
  --env ALLOWED_HOSTS=example.com \
  --env DATABASE_URL=postgresql://user:password@host:5432/dbname \
  --env SMTP__HOST=smtp.example.com \
  --env SMTP__PORT=587 \
  --env SMTP__SECURITY=starttls \
  --env SMTP__USERNAME=... \
  --env SMTP__PASSWORD=... \
  --publish 8000:8000 \
  fcacp
```

The server binds to `0.0.0.0:8000` by default. Override the port with the
`PORT` environment variable (the `CMD` in the Dockerfile respects `${PORT:-8000}`).

### Gunicorn tuning

`gunicorn.conf.py` is picked up automatically. The worker count defaults to
`cpu_count * 2 + 1`. Override via:

| Variable             | Default   | Description                                                     |
|----------------------|-----------|-----------------------------------------------------------------|
| `GUNICORN_HOST`      | `0.0.0.0` | Bind address                                                    |
| `GUNICORN_PORT`      | `8000`    | Bind port                                                       |
| `GUNICORN_LOG_LEVEL` | `info`    | Log verbosity (`debug`, `info`, `warning`, `error`, `critical`) |

---

## Database setup

Before the first run (and after each deployment that includes new migrations),
run:

```sh
docker run --env ... fcacp python manage.py migrate
```

Use the same environment variables as the main container. On most platforms this
is a one-off job or release command that runs before traffic is shifted to the
new version.

---

## TLS / Reverse proxy

The production settings trust the `X-Forwarded-Proto` header to detect HTTPS,
and `SECURE_SSL_REDIRECT` will redirect plain HTTP requests to HTTPS. This
assumes TLS is terminated at the edge (load balancer, reverse proxy, or platform
ingress) rather than inside the container.

If your platform does not set `X-Forwarded-Proto`, disable `SECURE_SSL_REDIRECT`
or terminate TLS inside the container instead.

HSTS is enabled with a one-year max-age including subdomains. Do not enable
this on a domain you do not fully control.

---

## Render

The current hosting target. Relevant settings are already in place
(`SECURE_PROXY_SSL_HEADER` is configured for Render's forwarded-proto header).

1. Create a new **Web Service** and point it at this repository.
2. Set **Environment** to **Docker**.
3. Add the environment variables from the table above under **Environment →
   Environment Variables**.
4. Add a **PostgreSQL** database in Render and copy the internal `DATABASE_URL`
   into the web service's env vars.
5. Under **Deploy → Pre-deploy command**, add:
   ```
   python manage.py migrate
   ```
6. Deploy. Render will build the image, run migrations, then start Gunicorn.

---

## Other platforms

Any platform that can run a Docker container will work. The key requirements are:

- PostgreSQL 13+ accessible from the container
- The environment variables above injected at runtime
- A reverse proxy or load balancer that sets `X-Forwarded-Proto: https`
- The `migrate` management command run as a pre-deploy or init step

For platforms that do not support Docker natively, run Gunicorn directly after
installing dependencies with `uv sync --group prod` and building assets with
`manage.py tailwind build && manage.py collectstatic`.
