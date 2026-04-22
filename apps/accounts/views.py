"""
Authentication and profile views for the accounts app.
"""

import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin

from .serializers import (
    ChangePasswordSerializer,
    GoogleAuthSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Register a new user account."""

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        # Trigger welcome email via Celery (imported lazily to avoid circular imports)
        try:
            from apps.notifications.tasks import send_welcome_email
            send_welcome_email.delay(str(user.id))
        except Exception:
            logger.warning("Could not dispatch welcome email for user %s", user.id)

        return Response(
            {
                "success": True,
                "message": _("Registration successful. Please verify your email."),
                "data": {
                    "user": UserProfileSerializer(user, context={"request": request}).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate and return JWT tokens."""

    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        return Response(
            {
                "success": True,
                "message": _("Login successful."),
                "data": {
                    "user": UserProfileSerializer(data["user"], context={"request": request}).data,
                    "access": data["access"],
                    "refresh": data["refresh"],
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Blacklist the refresh token to invalidate the session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "message": _("Refresh token is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": _("Logout successful.")},
            status=status.HTTP_200_OK,
        )


class UserProfileView(RetrieveUpdateAPIView):
    """Retrieve and update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response({"success": True, "data": serializer.data})


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"success": True, "message": _("Password changed successfully.")},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """Confirm email address using a token link."""

    permission_classes = [AllowAny]

    def get(self, request, key):
        from allauth.account.models import EmailConfirmationHMAC, EmailAddress
        from allauth.account.utils import send_email_confirmation

        try:
            confirmation = EmailConfirmationHMAC.from_key(key)
        except Exception:
            return Response(
                {"success": False, "message": _("Invalid or expired verification link.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        confirmation.confirm(request)
        user = confirmation.email_address.user
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        return Response(
            {"success": True, "message": _("Email verified successfully.")},
            status=status.HTTP_200_OK,
        )


class CustomerListView(ListAPIView):
    """List all non-staff customers (admin only)."""

    permission_classes = [IsAdmin]
    serializer_class = UserProfileSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        from django.db.models import Q
        qs = User.objects.filter(is_staff=False, is_superuser=False).order_by("-date_joined")
        search = self.request.query_params.get("search", "")
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data})


class GoogleLoginView(APIView):
    """Exchange a Google ID token for application JWT tokens."""

    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        return Response(
            {
                "success": True,
                "message": _("Google authentication successful."),
                "data": {
                    "user": UserProfileSerializer(data["user"], context={"request": request}).data,
                    "access": data["access"],
                    "refresh": data["refresh"],
                    "created": data["created"],
                },
            },
            status=status.HTTP_200_OK,
        )
