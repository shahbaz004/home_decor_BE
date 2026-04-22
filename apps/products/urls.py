from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet, TagViewSet

app_name = "products"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("tags", TagViewSet, basename="tag")
router.register("", ProductViewSet, basename="product")

urlpatterns = router.urls
