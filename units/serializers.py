from rest_framework import serializers
from django.utils import timezone
from units.models import Unit, UnitType, UnitStatus, UnitTenantHistory
from properties.models import Property
from properties.serializers import SimplePropertySerializer  # Add this import
from tenants.serializers import TenantReadSerializer

class UnitTenantHistorySerializer(serializers.ModelSerializer):
    tenant = TenantReadSerializer(read_only=True)

    class Meta:
        model = UnitTenantHistory
        fields = ['tenant', 'start_date', 'end_date']

# Remove the SimplePropertySerializer class from here since we moved it
class UnitReadSerializer(serializers.ModelSerializer):
    property = SimplePropertySerializer(source='property_fk')  # Using simplified serializer
    unit_type = serializers.ChoiceField(choices=UnitType.choices, source='type')
    unit_status = serializers.ChoiceField(choices=UnitStatus.choices, source='status')
    current_tenant = TenantReadSerializer(read_only=True)
    tenant_history = UnitTenantHistorySerializer(many=True, read_only=True)
    lease_status = serializers.SerializerMethodField()
    amenities = serializers.JSONField()
    features = serializers.JSONField()

    class Meta:
        model = Unit
        fields = [
            'id', 'unit_id', 'unit_number', 'property', 'unit_type', 'unit_status',
            'floor', 'size', 'rent', 'deposit', 'amenities', 'features',
            'current_tenant', 'lease_start_date', 'lease_end_date',
            'lease_status', 'tenant_history', 'created_at', 'updated_at'
        ]

    def get_lease_status(self, obj):
        return {
            'is_active': obj.check_lease_status,
            'days_remaining': (obj.lease_end_date - timezone.now()).days if obj.check_lease_status else None
        }

class UnitWriteSerializer(serializers.ModelSerializer):
    # Remove the property field since we're setting property_fk_id in perform_create
    # property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all(), required=True)
    unit_type = serializers.ChoiceField(choices=UnitType.choices, source='type')
    unit_status = serializers.ChoiceField(choices=UnitStatus.choices, source='status')
    amenities = serializers.JSONField(required=False)
    features = serializers.JSONField(required=False)

    class Meta:
        model = Unit
        fields = [
            'id', 'unit_number', 'unit_type', 'unit_status',
            'floor', 'size', 'rent', 'deposit', 'amenities', 'features',
            'current_tenant', 'lease_start_date', 'lease_end_date'
        ]
        read_only_fields = ['id', 'unit_id']

    def validate(self, data):
        # Validate lease dates
        start_date = data.get('lease_start_date')
        end_date = data.get('lease_end_date')
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'lease_end_date': 'Lease end date must be after start date'
            })

        # Validate tenant and lease dates consistency
        current_tenant = data.get('current_tenant')
        if current_tenant and not (start_date and end_date):
            raise serializers.ValidationError({
                'lease_dates': 'Lease dates are required when assigning a tenant'
            })

        return data

    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than 0")
        return value

    def validate_rent(self, value):
        if value < 0:
            raise serializers.ValidationError("Rent cannot be negative")
        return value

    def validate_deposit(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Deposit cannot be negative")
        return value