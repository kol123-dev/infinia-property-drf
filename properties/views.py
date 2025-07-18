from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import RoleBasedPermission
from properties.models import Property
from properties.serializers import PropertyReadSerializer, PropertyWriteSerializer
from agents.models import Agent
from property_manager.models import PropertyManager

class PropertyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Property.objects.select_related('landlord', 'landlord__user', 'agent', 'agent__user')
        
        if user.is_superuser or user.role == 'admin':
            return queryset.all()
        elif user.role == 'agent':
            return queryset.filter(agent__user=user)
        elif user.role == 'landlord':
            return queryset.filter(landlord__user=user)
        elif user.role == 'tenant':
            return queryset.filter(units__current_tenant__user=user)
        return Property.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PropertyReadSerializer
        return PropertyWriteSerializer

    def perform_create(self, serializer):
        user = self.request.user
        
        # Auto-assign agent based on user role
        if user.role == 'agent':
            try:
                agent = Agent.objects.get(user=user)
                serializer.save(agent=agent)
            except Agent.DoesNotExist:
                serializer.save()
        elif user.role == 'property_manager':
            try:
                property_manager = PropertyManager.objects.get(user=user)
                serializer.save(property_manager=property_manager)
            except PropertyManager.DoesNotExist:
                serializer.save()
        else:
            serializer.save()