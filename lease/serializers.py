from rest_framework import serializers
from lease.models import Lease, RenewalStatus
from properties.serializers import PropertyReadSerializer
from units.serializers import UnitReadSerializer
from tenants.serializers import TenantReadSerializer
from tenants.models import Tenant
from properties.models import Property
from units.models import Unit

class LeaseReadSerializer(serializers.ModelSerializer):
    tenant = TenantReadSerializer()
    property = PropertyReadSerializer()
    unit = UnitReadSerializer()
    renewal_status = serializers.ChoiceField(choices=RenewalStatus.choices, source='status')

    class Meta:
        model = Lease
        fields = [
            'id', 'lease_id', 'tenant', 'property', 'unit',
            'start_date', 'end_date', 'rent_amount', 'deposit_amount',
            'renewal_status', 'created_at'
        ]

class LeaseWriteSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=False,
        allow_null=True
    )
    property = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all(),
        required=False,
        allow_null=True
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        required=False,
        allow_null=True
    )
    renewal_status = serializers.ChoiceField(choices=RenewalStatus.choices, source='status')

    class Meta:
        model = Lease
        fields = [
            'id', 'lease_id', 'tenant', 'property', 'unit',
            'start_date', 'end_date', 'rent_amount', 'deposit_amount',
            'renewal_status'
        ]
        read_only_fields = ['id', 'lease_id']

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data

    def validate_rent_amount(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Rent amount cannot be negative")
        return value

    def validate_deposit_amount(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Deposit amount cannot be negative")
        return value