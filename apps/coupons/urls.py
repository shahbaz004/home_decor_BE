from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CouponViewSet, ValidateCouponView

app_name = "coupons"

router = DefaultRouter()
router.register("admin", CouponViewSet, basename="coupon_admin")

urlpatterns = [
    path("validate/", ValidateCouponView.as_view(), name="validate_coupon"),
] + router.urls
