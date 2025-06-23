# tenants/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from tenants.views import TenantViewSet, ContractViewSet
from landlords.views_full_create import CreateFullTenantView

router = SimpleRouter()
router.register(r'tenants', TenantViewSet)
router.register(r'contracts', ContractViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api/tenants/create_full/', CreateFullTenantView.as_view(), name='create_full_tenant'),
]