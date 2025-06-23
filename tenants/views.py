from rest_framework import viewsets
from tenants.models import Tenant, Contract
from tenants.serializers import TenantReadSerializer, TenantWriteSerializer, ContractReadSerializer, ContractWriteSerializer
from rental_backend.permissions import IsAdminOrLandlord, IsLandlordOrTenantReadOnly

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantWriteSerializer
    permission_classes = [IsLandlordOrTenantReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TenantReadSerializer
        return TenantWriteSerializer

    def get_queryset(self):
        if self.request.user.role == 'landlord':
            return Tenant.objects.filter(landlord__user=self.request.user)
        elif self.request.user.role == 'tenant':
            return Tenant.objects.filter(user=self.request.user)
        return Tenant.objects.none()


class ContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contracts.
    - Admins/Landlords: Full access to all contracts
    - Tenants: Read-only access to their own contract(s)
    """
    serializer_class = ContractWriteSerializer
    permission_classes = [IsAdminOrLandlord]
    queryset = Contract.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ContractReadSerializer
        return ContractWriteSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == 'landlord':
            # Landlord can see all contracts of tenants under their properties
            return Contract.objects.filter(tenant__landlord__user=user)

        elif user.role == 'tenant':
            # Tenant can only see their own contract
            try:
                # Assumes the User has a related Tenant profile
                tenant_profile = user.tenant_profile  # Adjust based on your actual relation
                return Contract.objects.filter(tenant=tenant_profile)
            except Tenant.DoesNotExist:
                return Contract.objects.none()

        return Contract.objects.none()
