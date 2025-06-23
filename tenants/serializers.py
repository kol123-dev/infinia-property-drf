from rest_framework import serializers
from tenants.models import Tenant, Contract
from units.models import Unit
from units.serializers import UnitReadSerializer
from landlords.serializers import LandlordReadSerializer
from landlords.models import Landlord


# --- TENANT SERIALIZERS ---
class TenantReadSerializer(serializers.ModelSerializer):
    unit = UnitReadSerializer(read_only=True)
    landlord = LandlordReadSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'user', 'landlord', 'unit',
            'move_in_date', 'expected_move_out_date', 'actual_move_out_date',
            'arrears', 'status', 'notes', 'created_at'
        ]


class TenantWriteSerializer(serializers.ModelSerializer):
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        required=False,
        allow_null=True
    )
    landlord = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.all()
    )

    class Meta:
        model = Tenant
        fields = [
            'id', 'user', 'landlord', 'unit',
            'move_in_date', 'expected_move_out_date', 'actual_move_out_date',
            'arrears', 'status', 'notes'
        ]
        read_only_fields = ['id']


# --- CONTRACT SERIALIZERS ---
class ContractReadSerializer(serializers.ModelSerializer):
    tenant = TenantReadSerializer()

    class Meta:
        model = Contract
        fields = [
            'id', 'tenant', 'start_date', 'end_date', 'file',
            'is_signed', 'signed_at', 'is_active', 'auto_renew', 'created_at'
        ]


class ContractWriteSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all()
    )

    class Meta:
        model = Contract
        fields = [
            'id', 'tenant', 'start_date', 'end_date', 'file',
            'is_signed', 'signed_at', 'is_active', 'auto_renew'
        ]
        read_only_fields = ['id', 'is_signed', 'signed_at']