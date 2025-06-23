from rest_framework import viewsets
from agents.models import Agent
from agents.serializers import AgentReadSerializer, AgentWriteSerializer
from rental_backend.permissions import IsAdminOrLandlord, IsAgent

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return AgentReadSerializer
        return AgentWriteSerializer
    def get_permissions(self):
        from rental_backend.permissions import IsAdmin
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrLandlord()]
        # Allow admin to list/retrieve all agents
        return [IsAgent() if not hasattr(self.request.user, 'role') or self.request.user.role != 'admin' else IsAdmin()]
    def get_queryset(self):
        user = self.request.user
        # Only allow agents to see themselves, admins/landlords see all
        if getattr(user, 'role', None) == 'agent':
            return Agent.objects.filter(user=user)
        return Agent.objects.all()
