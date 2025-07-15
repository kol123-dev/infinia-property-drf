# tenants/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from tenants.views import TenantViewSet, ContractViewSet

router = SimpleRouter()
router.register('', TenantViewSet, basename='tenant')
router.register('contracts', ContractViewSet, basename='contract')

urlpatterns = [
    path('', include(router.urls)),
]