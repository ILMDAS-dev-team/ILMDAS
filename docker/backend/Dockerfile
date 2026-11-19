# Production backend image (gunicorn). Used by docker/docker-compose.prod.yml later.
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ requirements/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/production.txt

FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1001 django && useradd --uid 1001 --gid django django

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=django:django . .

USER django

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    ILMDAS_SKIP_ENV_FILE=1

EXPOSE 8010

CMD ["sh", "-c", "gunicorn config.wsgi:application \
    --bind 0.0.0.0:8010 \
    --workers ${GUNICORN_WORKERS:-4} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -"]
