# property_manager/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from property_manager.views import PropertyManagerViewSet

router = SimpleRouter()
router.register('', PropertyManagerViewSet, basename='property-manager')

urlpatterns = [path('', include(router.urls))]