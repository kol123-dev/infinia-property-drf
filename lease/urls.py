from django.urls import path, include
from rest_framework.routers import SimpleRouter
from lease.views import LeaseViewSet

router = SimpleRouter()
router.register('', LeaseViewSet, basename='lease')

urlpatterns = [
    path('', include(router.urls)),
]