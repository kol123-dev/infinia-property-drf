from rest_framework import serializers
from agents.models import Agent
from accounts.serializers import UserReadSerializer
# Remove this line: from properties.serializers import PropertyReadSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class AgentReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    # Change this line to avoid circular import
    properties = serializers.SerializerMethodField()
    additional_contacts = serializers.JSONField(read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id', 'user', 'registration_number', 'tax_id',
            'street', 'city', 'postal_code', 'additional_contacts',
            'properties', 'created_at', 'updated_at'
        ]
    
    def get_properties(self, obj):
        # Import here to avoid circular import
        from properties.serializers import PropertyReadSerializer
        return PropertyReadSerializer(obj.managed_properties.all(), many=True).data

class AgentWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='agent')
    )
    additional_contacts = serializers.JSONField(required=False)
    properties = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id', 'user', 'registration_number', 'tax_id',
            'street', 'city', 'postal_code', 'additional_contacts',
            'properties'
        ]
        read_only_fields = ['id']

    def validate_additional_contacts(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Additional contacts must be a list")
        return value
