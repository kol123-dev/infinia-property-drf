from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from units.models import Unit, UnitStatus
from units.serializers import UnitReadSerializer, UnitWriteSerializer
from tenants.models import Tenant
from tenants.serializers import TenantReadSerializer
from django.shortcuts import get_object_or_404

class UnitViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Unit.objects.all()
        
        # Filter by property if property_pk is provided
        if 'property_pk' in self.kwargs:
            queryset = queryset.filter(property_fk=self.kwargs['property_pk'])
        
        # Filter by status if status parameter is provided
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UnitReadSerializer
        return UnitWriteSerializer

    def perform_create(self, serializer):
        if 'property_pk' in self.kwargs:
            serializer.save(property_fk_id=self.kwargs['property_pk'])
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def bulk(self, request, property_pk=None):
        if not property_pk:
            return Response(
                {"detail": "Property ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        units_data = request.data.get('units', [])
        if not units_data:
            return Response(
                {"detail": "No units provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UnitWriteSerializer(data=units_data, many=True)
        if serializer.is_valid():
            units = serializer.save(property_fk_id=property_pk)
            response_serializer = UnitReadSerializer(units, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total_units = Unit.objects.count()
        occupied_units = Unit.objects.filter(status=UnitStatus.OCCUPIED).count()
        vacant_units = Unit.objects.filter(status=UnitStatus.VACANT).count()
        maintenance_units = Unit.objects.filter(status=UnitStatus.MAINTENANCE).count()

        stats_data = {
            'total_units': total_units,
            'occupied_units': occupied_units,
            'vacant_units': vacant_units,
            'maintenance_units': maintenance_units,
            'occupancy_rate': (occupied_units / total_units * 100) if total_units > 0 else 0
        }

        return Response(stats_data)

    @action(detail=True, methods=['post'])
    def assign_tenant(self, request, pk=None):
        """Assign a tenant to a unit."""
        unit = self.get_object()
        tenant_id = request.data.get('tenant_id')
        lease_start_date = request.data.get('lease_start_date')
        lease_end_date = request.data.get('lease_end_date')

        if not tenant_id:
            return Response(
                {"detail": "tenant_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = get_object_or_404(Tenant, id=tenant_id)
        
        try:
            unit.assign_tenant(tenant, lease_start_date, lease_end_date)
            return Response(
                {"detail": "Tenant successfully assigned to unit"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def end_tenancy(self, request, pk=None):
        """End the current tenancy of a unit."""
        unit = self.get_object()
        end_date = request.data.get('end_date')

        try:
            unit.end_tenancy(end_date)
            return Response(
                {"detail": "Tenancy ended successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def tenant_history(self, request, pk=None):
        """Get the tenant history of a unit."""
        unit = self.get_object()
        history = unit.get_tenant_history()
        
        data = [{
            'tenant': TenantReadSerializer(entry.tenant).data if entry.tenant else None,
            'start_date': entry.start_date,
            'end_date': entry.end_date
        } for entry in history]
        
        return Response(data)