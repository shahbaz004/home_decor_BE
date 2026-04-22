"""
Pytest configuration and shared fixtures.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


User = get_user_model()


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """A standard (non-staff) user."""
    return User.objects.create_user(
        email="user@example.com",
        password="Test1234!",
        first_name="Test",
        last_name="User",
        is_email_verified=True,
    )


@pytest.fixture
def staff_user(db):
    """A staff/admin user."""
    return User.objects.create_user(
        email="admin@example.com",
        password="Admin1234!",
        first_name="Admin",
        last_name="User",
        is_staff=True,
        is_email_verified=True,
    )


@pytest.fixture
def auth_client(api_client, user):
    """API client authenticated as a regular user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    """API client authenticated as a staff user."""
    api_client.force_authenticate(user=staff_user)
    return api_client
