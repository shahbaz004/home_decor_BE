"""
Main URL configuration for home_decor project.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# ---------------------------------------------------------------------------
# API v1 URL patterns
# ---------------------------------------------------------------------------
api_v1_urlpatterns = [
    # Auth
    path("auth/", include("apps.accounts.urls")),
    # dj-rest-auth (password reset, social)
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    # JWT token endpoints
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Addresses
    path("addresses/", include("apps.addresses.urls")),
    # Products
    path("products/", include("apps.products.urls")),
    # Cart
    path("cart/", include("apps.cart.urls")),
    # Wishlist
    path("wishlist/", include("apps.wishlist.urls")),
    # Orders
    path("orders/", include("apps.orders.urls")),
    # Payments
    path("payments/", include("apps.payments.urls")),
    # Shipping
    path("shipping/", include("apps.shipping.urls")),
    # Coupons
    path("coupons/", include("apps.coupons.urls")),
    # Reviews
    path("reviews/", include("apps.reviews.urls")),
    # Notifications
    path("notifications/", include("apps.notifications.urls")),
    # Analytics
    path("analytics/", include("apps.analytics.urls")),
]

# ---------------------------------------------------------------------------
# Admin URL (can be overridden in production settings)
# ---------------------------------------------------------------------------
admin_url = getattr(settings, "ADMIN_URL", "admin/")

urlpatterns = [
    # Admin
    path(admin_url, admin.site.urls),
    # Social auth (allauth)
    path("accounts/", include("allauth.urls")),
    # API v1
    path("api/v1/", include(api_v1_urlpatterns)),
]

# ---------------------------------------------------------------------------
# Debug toolbar (development only)
# ---------------------------------------------------------------------------
if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
