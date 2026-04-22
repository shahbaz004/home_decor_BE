"""
Serializers for the accounts app.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Register a new user with email + password."""

    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "first_name": {"required": True},
        }

    def validate_email(self, value: str) -> str:
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return email

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    """Authenticate with email + password and return JWT tokens."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        from django.contrib.auth import authenticate

        email = attrs["email"].lower().strip()
        password = attrs["password"]
        user = authenticate(request=self.context.get("request"), email=email, password=password)

        if not user:
            raise serializers.ValidationError(_("Invalid email or password."))
        if not user.is_active:
            raise serializers.ValidationError(_("This account has been deactivated."))

        refresh = RefreshToken.for_user(user)
        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """Read/update the authenticated user's profile."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "avatar",
            "avatar_url",
            "date_of_birth",
            "gender",
            "is_email_verified",
            "oauth_provider",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "is_email_verified", "oauth_provider", "date_joined", "last_login"]
        extra_kwargs = {
            "avatar": {"write_only": True},
        }

    def get_avatar_url(self, obj) -> str | None:
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class ChangePasswordSerializer(serializers.Serializer):
    """Change the authenticated user's password."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": _("New passwords do not match.")})
        validate_password(attrs["new_password"], user=self.context["request"].user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class GoogleAuthSerializer(serializers.Serializer):
    """Exchange a Google ID token for application JWT tokens."""

    id_token = serializers.CharField()

    def validate_id_token(self, value: str):
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            from django.conf import settings

            idinfo = google_id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"],
            )
            return idinfo
        except Exception as exc:
            raise serializers.ValidationError(_("Invalid Google token.")) from exc

    def validate(self, attrs):
        idinfo = attrs["id_token"]

        email = idinfo.get("email")
        if not email:
            raise serializers.ValidationError(_("Could not retrieve email from Google token."))

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": idinfo.get("given_name", ""),
                "last_name": idinfo.get("family_name", ""),
                "is_email_verified": idinfo.get("email_verified", False),
                "oauth_provider": User.OAuthProvider.GOOGLE,
            },
        )

        if not created and user.oauth_provider != User.OAuthProvider.GOOGLE:
            # Allow linking accounts
            user.oauth_provider = User.OAuthProvider.GOOGLE
            user.is_email_verified = True
            user.save(update_fields=["oauth_provider", "is_email_verified"])

        refresh = RefreshToken.for_user(user)
        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "created": created,
        }


class TokenResponseSerializer(serializers.Serializer):
    """Serializes token responses for documentation purposes."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserProfileSerializer()
