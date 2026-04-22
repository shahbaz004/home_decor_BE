from django.urls import path

from .views import CartItemView, CartView, ClearCartView, MergeCartView

app_name = "cart"

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("items/", CartItemView.as_view(), name="cart_items"),
    path("items/<uuid:item_id>/", CartItemView.as_view(), name="cart_item_detail"),
    path("clear/", ClearCartView.as_view(), name="cart_clear"),
    path("merge/", MergeCartView.as_view(), name="cart_merge"),
]
