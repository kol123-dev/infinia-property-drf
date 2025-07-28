from django.urls import path, include
from rest_framework.routers import SimpleRouter
from tenants.views import TenantViewSet, ContractViewSet, TenantGroupViewSet

router = SimpleRouter()
router.register('', TenantViewSet, basename='tenant')
router.register('contracts', ContractViewSet, basename='contract')
router.register('groups', TenantGroupViewSet, basename='tenant-group')

urlpatterns = [
    path('', include(router.urls)),
]