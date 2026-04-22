from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CalculateShippingView,
    ShipmentTrackingView,
    ShippingRateViewSet,
    ShippingZoneViewSet,
)

app_name = "shipping"

router = DefaultRouter()
router.register("zones", ShippingZoneViewSet, basename="shipping_zone")
router.register("rates", ShippingRateViewSet, basename="shipping_rate")

urlpatterns = [
    path("calculate/", CalculateShippingView.as_view(), name="calculate_shipping"),
    path("tracking/<uuid:order_id>/", ShipmentTrackingView.as_view(), name="shipment_tracking"),
] + router.urls
