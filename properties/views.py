from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from properties.models import Property
from properties.serializers import PropertyReadSerializer, PropertyWriteSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Property.objects.select_related('landlord', 'landlord__user', 'agent', 'agent__user').all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PropertyReadSerializer
        return PropertyWriteSerializer