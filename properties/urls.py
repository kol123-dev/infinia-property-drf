# properties/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from properties.views import PropertyViewSet

router = SimpleRouter()
router.register(r'properties', PropertyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]