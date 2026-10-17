FROM node:22-bookworm-slim AS frontend-build

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_OTARM_API_BASE_URL=/api/v1
ENV VITE_OTARM_API_BASE_URL=${VITE_OTARM_API_BASE_URL}
RUN npm run build


FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
COPY --from=frontend-build /build/frontend/dist ./static

RUN useradd --create-home --uid 10001 otarm \
    && mkdir /data \
    && chown otarm:otarm /data

ENV PATH="/app/.venv/bin:${PATH}" \
    OTARM_DATABASE_URL=sqlite:////data/otarm.db \
    OTARM_STATIC_DIR=/app/static \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER otarm

EXPOSE 8000
VOLUME ["/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
