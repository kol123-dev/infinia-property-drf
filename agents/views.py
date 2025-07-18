from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import RoleBasedPermission
from agents.models import Agent
from agents.serializers import AgentReadSerializer, AgentWriteSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return AgentReadSerializer
        return AgentWriteSerializer
