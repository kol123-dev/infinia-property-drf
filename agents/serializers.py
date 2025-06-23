from rest_framework import serializers
from agents.models import Agent
from accounts.serializers import UserReadSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class AgentReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    class Meta:
        model = Agent
        fields = ['id', 'user', 'created_at']

class AgentWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='agent'))
    class Meta:
        model = Agent
        fields = ['id', 'user']
        read_only_fields = ['id']
