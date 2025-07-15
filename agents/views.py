from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from agents.models import Agent
from agents.serializers import AgentReadSerializer, AgentWriteSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return AgentReadSerializer
        return AgentWriteSerializer
