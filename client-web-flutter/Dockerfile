ARG REGISTRY_PREFIX_GHCR
ARG REGISTRY_PREFIX_DOCKER_HUB

FROM ${REGISTRY_PREFIX_GHCR}cirruslabs/flutter:3.41.2 AS builder

WORKDIR /app

# Flutter warns about running as root, but this is safe in a build-only container.
# Resolve dependencies first for layer caching.
COPY pubspec.yaml pubspec.lock ./
RUN --mount=type=cache,target=/root/.pub-cache flutter pub get

COPY . .
RUN --mount=type=cache,target=/app/.dart_tool \
    --mount=type=cache,target=/root/.pub-cache \
    flutter build web --base-href /flutter/

# Redeclare ARGs after FROM since they don't persist across stages
ARG REGISTRY_PREFIX_DOCKER_HUB

FROM ${REGISTRY_PREFIX_DOCKER_HUB}alpine:3.21 AS runner

WORKDIR /output

# Copy built web assets directly to output directory
COPY --from=builder /app/build/web/ /output/

# Default command (can be overridden at runtime)
CMD ["sh", "-c", "echo 'Build complete. Assets in /output/'"]
