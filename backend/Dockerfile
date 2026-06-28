# Pinned to bookworm (Debian 12) — Playwright officially supports this; the
# unpinned `slim` tag now resolves to trixie (Debian 13), which `playwright
# install --with-deps` doesn't have a package list for and falls back to
# Ubuntu 20.04 deps that aren't all available on trixie.
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Playwright runtime: split into two layers so a flaky Chromium CDN download
# doesn't invalidate the (slow) apt step on retry.
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget gnupg ca-certificates \
    && python -m playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/*
RUN python -m playwright install chromium

COPY . .

EXPOSE 8000
# Start the web server directly. Migrations must NOT run here: this command runs
# on every cold-start wake (not just on deploy), and concurrent wakes would each
# re-run the full DDL migration and deadlock each other on table locks, leaving
# the API permanently unable to start. Run migrations as a deliberate step
# instead (Render Pre-Deploy/Shell, Heroku release phase, or `python migrate.py`).
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
