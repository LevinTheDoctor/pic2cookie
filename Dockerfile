# syntax=docker/dockerfile:1

# --- Frontend -----------------------------------------------------------------
FROM --platform=$BUILDPLATFORM node:24-alpine AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Python dependencies ----------------------------------------------------------
FROM python:3.15-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-extras --no-install-project
COPY README.md ./
COPY pic2cookie/ pic2cookie/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-extras --no-editable

# --- Runtime ------------------------------------------------------------------------
FROM python:3.15-slim
LABEL org.opencontainers.image.title="Pic2Cookie" \
      org.opencontainers.image.description="Turn a picture into a 3D-printable cookie cutter"
RUN useradd --create-home --uid 10001 pic2cookie
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=frontend /src/frontend/dist /app/frontend/dist
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIC2COOKIE_FRONTEND_DIR=/app/frontend/dist \
    PIC2COOKIE_STORAGE__PATH=/data \
    PIC2COOKIE_HOST=0.0.0.0 \
    PIC2COOKIE_PORT=8000
RUN mkdir /data && chown pic2cookie /data
USER pic2cookie
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["pic2cookie", "serve"]
