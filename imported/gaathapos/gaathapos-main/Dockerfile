# --- Build Stage ---
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements*.txt ./
RUN if [ -f requirements-production.txt ]; then pip install --no-cache-dir -r requirements-production.txt; else pip install -r requirements.txt; fi
RUN pip install --no-cache-dir gunicorn psycopg2-binary

# --- Final Stage ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    APP_ENV=production \
    PORT=3006 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN addgroup --system app && adduser --system --group app

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN chown -R app:app /app /opt/venv
USER app

EXPOSE 3006

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3006/health', timeout=5).read()" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD gunicorn --workers ${GUNICORN_WORKERS:-4} --bind 0.0.0.0:${PORT:-3006} wsgi:app