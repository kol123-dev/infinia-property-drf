# properties/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers
from properties.views import PropertyViewSet
from units.views import UnitViewSet

router = SimpleRouter()
router.register('', PropertyViewSet, basename='property')

# Create a nested router for units
property_router = routers.NestedSimpleRouter(router, '', lookup='property')
property_router.register('units', UnitViewSet, basename='property-units')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(property_router.urls)),
]