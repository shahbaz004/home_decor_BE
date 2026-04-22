"""
Settings for running inside Docker (development mode, no debug-toolbar dep).
"""

import os
from datetime import timedelta

from .base import *  # noqa: F401, F403

DEBUG = True
SECRET_KEY = "docker-dev-secret-key-change-in-production"
SENTRY_DSN = ""  # disable Sentry in Docker dev
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CORS_ALLOW_ALL_ORIGINS = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    }
}

# cached_db writes through cache AND DB so Django's login cycle_key()
# (delete old key → create new) doesn't leave the middleware trying to
# save a key that no longer exists in the cache-only backend.
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# Use local filesystem — no Cloudinary credentials needed
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# Run Celery tasks eagerly so worker container isn't required for basic dev
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

REST_AUTH = {
    **REST_AUTH,  # noqa: F405
    "JWT_AUTH_SECURE": False,
    "JWT_AUTH_HTTPONLY": False,
}
