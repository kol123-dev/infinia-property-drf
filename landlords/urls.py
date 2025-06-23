# landlords/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from landlords.views import LandlordViewSet
from landlords.views_full_create import CreateFullLandlordView, CreateFullPropertyManagerView

router = SimpleRouter()
router.register(r'', LandlordViewSet, basename='landlord')

urlpatterns = [
    path('', include(router.urls)),
    path('create_full/', CreateFullLandlordView.as_view(), name='create_full_landlord'),
    path('create_full_property_manager/', CreateFullPropertyManagerView.as_view(), name='create_full_property_manager'),
]