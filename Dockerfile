FROM ghcr.io/astral-sh/uv:trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_INSTALL_DIR=/python
ENV UV_PYTHON_PREFERENCE=only-managed

RUN uv python install

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --group prod

COPY . /app

RUN set -ex; \
    mkdir -p assets; \
    uv run manage.py collectstatic --no-input

FROM debian:trixie-slim

RUN set -ex; \
    groupadd --system --gid 999 nonroot; \
    useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /python /python
COPY --from=builder --chown=nonroot:nonroot /app /app

USER nonroot
WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["gunicorn", "fcacp.wsgi"]
