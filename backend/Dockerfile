# Backend AmanDjiwa (FastAPI + migrasi Alembic). Dibangun dari docker-compose.yml di root repo.
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/srv/venv \
    PATH=/srv/venv/bin:$PATH PYTHONUNBUFFERED=1

# app/settings.py: ROOT = /srv → model ONNX dicari di /srv/ml/models (di-mount dari compose).
WORKDIR /srv/backend
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

RUN useradd --system --no-create-home app
USER app
EXPOSE 8000
# Migrasi dulu, baru API. Access log uvicorn dimatikan di app (path bisa memuat token, §7).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
