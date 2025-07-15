# units/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from units.views import UnitViewSet

router = SimpleRouter()
router.register('', UnitViewSet, basename='unit')  # Remove r'units' prefix

urlpatterns = [
    path('', include(router.urls)),
]