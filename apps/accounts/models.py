"""
Custom user model using email as the primary identifier.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser – uses email instead of username."""

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set."))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.  Email is the unique identifier; there is no username.
    """

    class Gender(models.TextChoices):
        MALE = "M", _("Male")
        FEMALE = "F", _("Female")
        OTHER = "O", _("Other")
        PREFER_NOT = "N", _("Prefer not to say")

    class OAuthProvider(models.TextChoices):
        EMAIL = "email", _("Email")
        GOOGLE = "google", _("Google")
        FACEBOOK = "facebook", _("Facebook")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    phone = models.CharField(_("phone number"), max_length=20, blank=True, db_index=True)
    avatar = models.ImageField(
        _("avatar"), upload_to="avatars/", null=True, blank=True
    )
    date_of_birth = models.DateField(_("date of birth"), null=True, blank=True)
    gender = models.CharField(
        _("gender"),
        max_length=1,
        choices=Gender.choices,
        default=Gender.PREFER_NOT,
        blank=True,
    )
    is_email_verified = models.BooleanField(_("email verified"), default=False)
    oauth_provider = models.CharField(
        _("OAuth provider"),
        max_length=20,
        choices=OAuthProvider.choices,
        default=OAuthProvider.EMAIL,
    )
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login = models.DateTimeField(_("last login"), null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.first_name or self.email.split("@")[0]
