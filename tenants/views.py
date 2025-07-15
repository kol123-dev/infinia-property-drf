from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from tenants.models import Tenant, Contract
from tenants.serializers import TenantReadSerializer, TenantWriteSerializer, ContractReadSerializer, ContractWriteSerializer

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TenantReadSerializer
        return TenantWriteSerializer

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ContractReadSerializer
        return ContractWriteSerializer
