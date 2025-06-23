from rest_framework import viewsets
from properties.models import Property
from properties.serializers import PropertyReadSerializer, PropertyWriteSerializer
from rental_backend.permissions import IsAdminOrLandlord, IsAgent
from landlords.models import Landlord
from rest_framework.exceptions import PermissionDenied

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertyWriteSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAgent()]
        return [IsAdminOrLandlord()]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PropertyReadSerializer
        return PropertyWriteSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Property.objects.none()
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return Property.objects.all()
        if getattr(user, 'role', None) == 'agent':
            return Property.objects.filter(landlord__agent=user)
        if getattr(user, 'role', None) == 'landlord':
            return Property.objects.filter(landlord__user=user)
        return Property.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        landlord_id = self.request.data.get('landlord')
        if getattr(user, 'role', None) == 'agent':
            # Agent can only create for landlords they manage
            if not landlord_id:
                raise PermissionDenied('Landlord must be specified.')
            try:
                landlord = Landlord.objects.get(id=landlord_id, agent=user)
            except Landlord.DoesNotExist:
                raise PermissionDenied('You can only create properties for landlords you manage.')
        elif getattr(user, 'role', None) == 'landlord':
            # Landlord can only create for themselves
            try:
                landlord = Landlord.objects.get(user=user)
            except Landlord.DoesNotExist:
                raise PermissionDenied('Landlord profile not found.')
        else:
            raise PermissionDenied('Not allowed.')
        serializer.save(landlord=landlord)