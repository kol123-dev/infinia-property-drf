from rest_framework import serializers
from property_manager.models import PropertyManager
from accounts.serializers import UserReadSerializer
from properties.serializers import PropertyReadSerializer
from properties.models import Property  # Add this import
from django.contrib.auth import get_user_model

User = get_user_model()

class PropertyManagerReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    assigned_properties = PropertyReadSerializer(many=True, read_only=True)
    shift_hours = serializers.JSONField(read_only=True)

    class Meta:
        model = PropertyManager
        fields = [
            'id', 'manager_id', 'user', 'assigned_properties',
            'start_date', 'end_date', 'shift_hours', 'emergency_phone',
            'address', 'contract_url', 'id_document_url', 'created_at'
        ]

class PropertyManagerWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='property_manager')
    )
    assigned_properties = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Property.objects.all(),
        required=False
    )
    shift_hours = serializers.JSONField(required=False)

    class Meta:
        model = PropertyManager
        fields = [
            'id', 'manager_id', 'user', 'assigned_properties',
            'start_date', 'end_date', 'shift_hours', 'emergency_phone',
            'address', 'contract_url', 'id_document_url'
        ]
        read_only_fields = ['id', 'manager_id']

    def validate_emergency_phone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Emergency phone must start with '+'")
        return value

    def validate_shift_hours(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Shift hours must be a dictionary")
        return value

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data
