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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
