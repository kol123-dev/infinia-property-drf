from django.urls import path, include
from rest_framework.routers import SimpleRouter
from property_manager.views import PropertyManagerViewSet
from property_manager.views_full_create import CreateFullPropertyManagerView

router = SimpleRouter()
router.register(r'', PropertyManagerViewSet, basename='property_manager')

urlpatterns = [
    path('', include(router.urls)),
    path('create_full/', CreateFullPropertyManagerView.as_view(), name='create_full_property_manager'),
]
