# units/views.py
from rest_framework import viewsets
from units.models import Unit
from units.serializers import UnitReadSerializer, UnitWriteSerializer
from rental_backend.permissions import IsAdminOrLandlord, IsAgent
from properties.models import Property
from landlords.models import Landlord
from rest_framework.exceptions import PermissionDenied


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAgent()]
        return [IsAdminOrLandlord()]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UnitReadSerializer
        return UnitWriteSerializer

    def perform_create(self, serializer):
        user = self.request.user
        property_id = self.request.data.get('property')
        if not property_id:
            raise PermissionDenied('Property must be specified.')
        try:
            property_obj = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            raise PermissionDenied('Invalid property specified.')
        if getattr(user, 'role', None) == 'agent':
            # Agent can only create units for properties of landlords they manage
            if not property_obj.landlord.agent == user:
                raise PermissionDenied('You can only create units for properties of landlords you manage.')
        elif getattr(user, 'role', None) == 'landlord':
            # Landlord can only create units for their own properties
            if not property_obj.landlord.user == user:
                raise PermissionDenied('You can only create units for your own properties.')
        else:
            raise PermissionDenied('Not allowed.')
        serializer.save(property=property_obj)