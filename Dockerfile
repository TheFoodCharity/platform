FROM ghcr.io/astral-sh/uv:trixie-slim AS builder

ARG NODEJS_VERSION=v24.15.0
ARG NODEJS_ARCH=x64

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_INSTALL_DIR=/python
ENV UV_PYTHON_PREFERENCE=only-managed

ENV DJANGO_SETTINGS_MODULE=fcacp.settings.build

RUN set -ex; \
    apt-get update; \
    apt-get install --no-install-recommends --yes \
      ca-certificates \
      curl \
      xz-utils; \
    curl \
      --silent --location --output /tmp/nodejs.tar.xz \
      https://nodejs.org/dist/${NODEJS_VERSION}/node-${NODEJS_VERSION}-linux-${NODEJS_ARCH}.tar.xz; \
    tar --strip-components 1 -C /usr/local -xf /tmp/nodejs.tar.xz

WORKDIR /app

RUN --mount=type=bind,source=theme/static_src/package.json,target=theme/static_src/package.json \
    --mount=type=bind,source=theme/static_src/package-lock.json,target=theme/static_src/package-lock.json \
    set -ex; \
    cd theme/static_src; \
    npm clean-install

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    set -ex; \
    uv python install; \
    uv sync --locked --group prod

COPY . /app

RUN set -ex; \
    mkdir -p assets; \
    uv run manage.py tailwind build; \
    uv run manage.py collectstatic --no-input

FROM debian:trixie-slim

RUN set -ex; \
    apt-get update; \
    apt-get install --yes --no-install-recommends ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    groupadd --system --gid 999 nonroot; \
    useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /python /python
COPY --from=builder --chown=nonroot:nonroot /app /app

USER nonroot
WORKDIR /app

ENV DJANGO_SETTINGS_MODULE=fcacp.settings.production
ENV PATH="/app/.venv/bin:$PATH"

CMD ["gunicorn", "fcacp.wsgi"]
