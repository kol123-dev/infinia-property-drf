from rest_framework import viewsets
from property_manager.models import PropertyManager
from property_manager.serializers import PropertyManagerReadSerializer, PropertyManagerWriteSerializer
from rental_backend.permissions import IsAdminOrLandlord, IsAgent

class PropertyManagerViewSet(viewsets.ModelViewSet):
    queryset = PropertyManager.objects.all()
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PropertyManagerReadSerializer
        return PropertyManagerWriteSerializer
    def get_permissions(self):
        from rental_backend.permissions import IsAdmin
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrLandlord()]
        # Allow admin to list/retrieve all property managers
        return [IsAgent() if not hasattr(self.request.user, 'role') or self.request.user.role != 'admin' else IsAdmin()]
    def get_queryset(self):
        user = self.request.user
        # Only allow property managers to see themselves, admins/landlords see all
        if getattr(user, 'role', None) == 'property_manager':
            return PropertyManager.objects.filter(user=user)
        return PropertyManager.objects.all()
