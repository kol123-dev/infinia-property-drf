from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from tenants.models import Tenant, Contract
from tenants.serializers import TenantReadSerializer, TenantWriteSerializer, ContractReadSerializer, ContractWriteSerializer
from accounts.permissions import RoleBasedPermission
from tenants.models import Tenant, TenantGroup
from tenants.serializers import (
    TenantReadSerializer, TenantWriteSerializer,
    TenantGroupReadSerializer, TenantGroupWriteSerializer
)

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


class TenantGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'landlord':
            return TenantGroup.objects.filter(landlord=user.landlord_profile)
        elif user.role == 'agent':
            return TenantGroup.objects.filter(landlord__in=user.agent_profile.managed_landlords.all())
        return TenantGroup.objects.none()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TenantGroupWriteSerializer
        return TenantGroupReadSerializer
    
    def perform_create(self, serializer):
        if self.request.user.role == 'landlord':
            serializer.save(landlord=self.request.user.landlord_profile)
        else:
            serializer.save()