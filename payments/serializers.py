from rest_framework import serializers
from payments.models import Payment, PaymentReceipt
from tenants.models import Tenant
from tenants.serializers import TenantReadSerializer
from units.serializers import UnitReadSerializer
from landlords.serializers import LandlordReadSerializer
from units.models import Unit
from landlords.models import Landlord


# --- PAYMENT SERIALIZERS ---
class PaymentReadSerializer(serializers.ModelSerializer):
    tenant = TenantReadSerializer()
    unit = UnitReadSerializer()
    landlord = LandlordReadSerializer()

    class Meta:
        model = Payment
        fields = [
            'id', 'landlord', 'tenant', 'unit', 'amount', 'payment_date',
            'payment_method', 'reference_code', 'total_balance',
            'status', 'notes', 'created_at'
        ]


class PaymentWriteSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=False,
        allow_null=True
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        required=False,
        allow_null=True
    )
    landlord = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.all()
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'landlord', 'tenant', 'unit', 'amount', 'payment_date',
            'payment_method', 'reference_code', 'total_balance',
            'status', 'notes'
        ]
        read_only_fields = ['id', 'total_balance', 'landlord']


# --- RECEIPT SERIALIZERS ---
class PaymentReceiptReadSerializer(serializers.ModelSerializer):
    payment = PaymentReadSerializer()

    class Meta:
        model = PaymentReceipt
        fields = ['id', 'payment', 'receipt_number', 'generated_at', 'status', 'notes']


class PaymentReceiptWriteSerializer(serializers.ModelSerializer):
    payment = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all()
    )

    class Meta:
        model = PaymentReceipt
        fields = ['id', 'payment', 'receipt_number', 'status', 'notes']
        read_only_fields = ['id']