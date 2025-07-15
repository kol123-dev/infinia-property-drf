from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from property_manager.models import PropertyManager
from property_manager.serializers import PropertyManagerReadSerializer, PropertyManagerWriteSerializer

class PropertyManagerViewSet(viewsets.ModelViewSet):
    queryset = PropertyManager.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PropertyManagerReadSerializer
        return PropertyManagerWriteSerializer
