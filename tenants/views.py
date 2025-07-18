from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from tenants.models import Tenant, Contract
from tenants.serializers import TenantReadSerializer, TenantWriteSerializer, ContractReadSerializer, ContractWriteSerializer
from accounts.permissions import RoleBasedPermission

class TenantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Tenant.objects.select_related('user', 'current_unit', 'landlord')
        
        # Filter based on user role
        if user.role == 'landlord':
            # Landlords can only see their own tenants
            queryset = queryset.filter(landlord__user=user)
        elif user.role == 'agent':
            # Agents can see tenants of properties they manage
            queryset = queryset.filter(current_unit__property_fk__agent__user=user)
        
        # Additional property filter if property_id is provided
        property_id = self.request.query_params.get('property')
        if property_id:
            queryset = queryset.filter(current_unit__property_fk_id=property_id)
        
        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TenantReadSerializer
        return TenantWriteSerializer

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ContractReadSerializer
        return ContractWriteSerializer