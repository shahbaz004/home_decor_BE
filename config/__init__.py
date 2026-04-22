"""
Config package – import Celery app so it is initialised when Django starts.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
