"""
Abstract base models shared across the project.
"""

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model providing self-managed ``created_at`` and
    ``updated_at`` fields plus a UUID primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Only run full_clean on full saves (not partial update_fields saves)
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)


class SoftDeleteManager(models.Manager):
    """Returns only non-deleted objects by default."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Returns all objects, including soft-deleted ones."""

    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(TimeStampedModel):
    """
    Abstract model adding soft-delete behaviour. Objects are hidden from the
    default queryset but not removed from the database.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False):
        """Soft-delete: set deleted_at instead of removing the row."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently remove the object from the database."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
