#!/usr/bin/env bash
# -----------------------------------------------------------------------
# Docker entrypoint for the Home Decor backend.
# Runs migrations, collects static files, then starts Gunicorn.
# -----------------------------------------------------------------------

set -euo pipefail

echo "======================================================"
echo "  Home Decor Backend – Starting"
echo "======================================================"

# ---------------------------------------------------------------------------
# 1. Wait for the database to be ready
# ---------------------------------------------------------------------------
echo "[INFO] Waiting for database..."
MAX_RETRIES=30
RETRY_INTERVAL=2
retry=0

until python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE:-config.settings.prod}')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; do
    retry=$((retry + 1))
    if [ "$retry" -ge "$MAX_RETRIES" ]; then
        echo "[ERROR] Database not reachable after ${MAX_RETRIES} retries. Aborting."
        exit 1
    fi
    echo "[INFO]  Database not ready, waiting ${RETRY_INTERVAL}s... (attempt ${retry}/${MAX_RETRIES})"
    sleep "$RETRY_INTERVAL"
done

echo "[INFO] Database is ready."

# ---------------------------------------------------------------------------
# 2. Apply migrations
# ---------------------------------------------------------------------------
echo "[INFO] Running database migrations..."
python manage.py migrate --noinput

# ---------------------------------------------------------------------------
# 3. Collect static files
# ---------------------------------------------------------------------------
echo "[INFO] Collecting static files..."
python manage.py collectstatic --noinput --clear

# ---------------------------------------------------------------------------
# 4. Create a superuser if environment variables are provided
# ---------------------------------------------------------------------------
if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "[INFO] Creating/verifying superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = '${DJANGO_SUPERUSER_EMAIL}'
password = '${DJANGO_SUPERUSER_PASSWORD}'
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print('Superuser created.')
else:
    print('Superuser already exists, skipping.')
"
fi

# ---------------------------------------------------------------------------
# 5. Start Gunicorn
# ---------------------------------------------------------------------------
WORKERS="${GUNICORN_WORKERS:-4}"
THREADS="${GUNICORN_THREADS:-2}"
TIMEOUT="${GUNICORN_TIMEOUT:-120}"
BIND="${GUNICORN_BIND:-0.0.0.0:8000}"

echo "[INFO] Starting Gunicorn on ${BIND} with ${WORKERS} workers and ${THREADS} threads..."

exec gunicorn config.wsgi:application \
    --bind "$BIND" \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --timeout "$TIMEOUT" \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --log-level "${GUNICORN_LOG_LEVEL:-info}" \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --forwarded-allow-ips='*'
