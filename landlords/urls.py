from django.urls import path, include
from rest_framework.routers import SimpleRouter
from landlords.views import LandlordViewSet

router = SimpleRouter()
router.register('', LandlordViewSet, basename='landlord')

urlpatterns = [path('', include(router.urls))]