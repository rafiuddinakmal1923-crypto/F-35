# API, job scheduler, pipeline and CLI in one image (lite profile).
# Debian 12: Playwright 1.52 installs Chromium dependencies by Debian 12 package names (fails on Debian 13).
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY backend/ /app/backend/
COPY config/ /app/config/
COPY data/ /app/data/
COPY reports/ /app/reports/
COPY scripts/ /app/scripts/

ENV VG_CONFIG_DIR=/app/config \
    DATA_ROOT=/data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)" || exit 1
# Migrations are idempotent, so a fresh `docker compose up` never serves an empty schema.
CMD ["sh", "-c", "python -m voltguard migrate && exec uvicorn voltguard.api.main:app --host 0.0.0.0 --port 8000"]
