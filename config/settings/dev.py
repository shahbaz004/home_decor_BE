"""
Development settings for home_decor project.
"""

from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = "dev-secret-key-not-for-production-use-only"
ALLOWED_HOSTS = ["*"]

# ---------------------------------------------------------------------------
# Database – use SQLite for quick local dev or PostgreSQL if configured
# ---------------------------------------------------------------------------
import os

if os.environ.get("USE_SQLITE", "false").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

# ---------------------------------------------------------------------------
# Email – print to console
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# CORS – allow all in development
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Debug toolbar
# ---------------------------------------------------------------------------
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1", "localhost"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    "SHOW_COLLAPSED": True,
}

# ---------------------------------------------------------------------------
# Cache – use dummy cache in dev so caching never hides issues
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# ---------------------------------------------------------------------------
# Media – local filesystem in dev
# ---------------------------------------------------------------------------
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ---------------------------------------------------------------------------
# JWT – longer tokens for convenience during development
# ---------------------------------------------------------------------------
from datetime import timedelta

SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# ---------------------------------------------------------------------------
# Celery – run tasks eagerly in dev so no broker is needed
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# Logging – show all SQL queries when DEBUG is True
# ---------------------------------------------------------------------------
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if os.environ.get("LOG_SQL") else "WARNING",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Security – relaxed for local dev
# ---------------------------------------------------------------------------
REST_AUTH = {
    **REST_AUTH,  # noqa: F405
    "JWT_AUTH_SECURE": False,
    "JWT_AUTH_HTTPONLY": False,
}
