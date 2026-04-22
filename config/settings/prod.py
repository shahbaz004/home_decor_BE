"""
Production settings for home_decor project.
"""

from .base import *  # noqa: F401, F403
from decouple import config

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = False

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = "strict-origin-when-cross-origin"

# ---------------------------------------------------------------------------
# Database – production PostgreSQL with connection pooling
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
            "sslmode": config("DB_SSLMODE", default="require"),
        },
    }
}

# ---------------------------------------------------------------------------
# Cloudinary – production media storage
# ---------------------------------------------------------------------------
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# ---------------------------------------------------------------------------
# Cache – Redis with higher timeout in production
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 1000,
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
        },
        "KEY_PREFIX": "homedecor_prod",
        "TIMEOUT": 600,
    }
}

# ---------------------------------------------------------------------------
# Email – SendGrid in production
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
REST_AUTH = {
    **REST_AUTH,  # noqa: F405
    "JWT_AUTH_SECURE": True,
    "JWT_AUTH_HTTPONLY": True,
}

# ---------------------------------------------------------------------------
# Logging – structured logging in production
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(message)s",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security.DisallowedHost": {
            "handlers": ["console"],
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Content Security Policy (add django-csp to requirements if desired)
# ---------------------------------------------------------------------------
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_STYLE_SRC = ("'self'", "fonts.googleapis.com")
# CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")

# ---------------------------------------------------------------------------
# Admin URL (obfuscate in production)
# ---------------------------------------------------------------------------
ADMIN_URL = config("ADMIN_URL", default="admin/")

# ---------------------------------------------------------------------------
# ADMINS – receives 500 error emails
# ---------------------------------------------------------------------------
ADMINS = [
    ("Admin", config("ADMIN_EMAIL", default="admin@homedecor.com")),
]
MANAGERS = ADMINS

# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------
CONN_MAX_AGE = 60
