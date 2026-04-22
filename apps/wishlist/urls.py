from django.urls import path

from .views import MoveToCartView, WishlistItemView, WishlistView

app_name = "wishlist"

urlpatterns = [
    path("", WishlistView.as_view(), name="wishlist"),
    path("<uuid:item_id>/", WishlistItemView.as_view(), name="wishlist_item"),
    path("move-to-cart/", MoveToCartView.as_view(), name="move_to_cart"),
]
