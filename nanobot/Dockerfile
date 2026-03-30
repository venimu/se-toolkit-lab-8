# Adapted from backend/Dockerfile
# Also see https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads - use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace root files for uv sync (from workspace additional_context)
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy nanobot project files
COPY pyproject.toml /app/nanobot/pyproject.toml

# Sync dependencies (nanobot + mcp-lms + webchat deps)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package nanobot

# Copy the rest of the nanobot project
COPY . /app/nanobot

# Note: Editable workspace dependencies (mcp-lms, nanobot-webchat, mcp-webchat)
# will be installed at runtime via bind mounts. The first sync installed all PyPI dependencies.
# The entrypoint will handle the rest.

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

# Set environment variables for Python and application
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Make sure we use UTF-8 encoding
ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends gosu python3-pip && rm -rf /var/lib/apt/lists/*

# Accept build args for user IDs (to match host user for bind mounts)
ARG APP_UID=999
ARG APP_GID=999

# Setup a non-root user with configurable UID/GID
RUN groupadd --system --gid ${APP_GID} appgroup \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

# Copy the application from the builder
COPY --from=builder --chown=appuser:appgroup /app /app

# Create writable directory for nanobot workspace
RUN mkdir -p /app/nanobot/workspace && chown -R appuser:appgroup /app/nanobot/workspace

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/home/appuser/.local/lib/python3.14/site-packages"

# Use the app user to run our application
USER appuser

# Set working directory
WORKDIR /app/nanobot

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${NANOBOT_GATEWAY_CONTAINER_PORT:-18790}/health')" || exit 1

ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
