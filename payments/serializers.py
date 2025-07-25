from rest_framework import serializers
from django.utils import timezone  # Add this import
from payments.models import (
    Payment, PaymentReceipt, PaymentStatus, PaymentMethod,
    MpesaTransaction, BankTransaction, CashPayment
)
from properties.serializers import PropertyReadSerializer
from tenants.serializers import TenantReadSerializer
from units.serializers import UnitReadSerializer
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit
from accounts.serializers import UserReadSerializer
from .models import Payment, MpesaTransaction, BankTransaction, CashPayment, PaymentReceipt, Invoice, InvoiceItem

class MpesaTransactionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaTransaction
        fields = [
            'id', 'transaction_id', 'phone_number', 'amount',
            'paybill_number', 'account_reference', 'transaction_date',
            'status', 'result_code', 'result_description'
        ]

class MpesaTransactionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaTransaction
        fields = [
            'id', 'payment', 'transaction_id', 'phone_number', 'amount',
            'paybill_number', 'account_reference', 'transaction_date',
            'status', 'result_code', 'result_description'
        ]
        read_only_fields = ['id']

class BankTransactionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = [
            'id', 'bank_name', 'account_number', 'reference_number',
            'transfer_date', 'amount', 'status', 'verification_status',
            'ipn_response'
        ]

class BankTransactionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = [
            'id', 'payment', 'bank_name', 'account_number', 'reference_number',
            'transfer_date', 'amount', 'status', 'verification_status',
            'ipn_response'
        ]
        read_only_fields = ['id']

class CashPaymentReadSerializer(serializers.ModelSerializer):
    received_by = UserReadSerializer()

    class Meta:
        model = CashPayment
        fields = [
            'id', 'received_by', 'amount', 'receipt_number',
            'notes'
        ]

class CashPaymentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashPayment
        fields = [
            'id', 'payment', 'received_by', 'amount', 'receipt_number',
            'notes'
        ]
        read_only_fields = ['id', 'receipt_number']

class PaymentReadSerializer(serializers.ModelSerializer):
    property = PropertyReadSerializer()
    tenant = TenantReadSerializer()
    unit = UnitReadSerializer()
    payment_status = serializers.ChoiceField(choices=PaymentStatus.choices, source='status')
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, source='method')
    mpesa_details = MpesaTransactionReadSerializer(read_only=True)
    bank_details = BankTransactionReadSerializer(read_only=True)
    cash_details = CashPaymentReadSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'property', 'tenant', 'unit', 'due_date',
            'paid_date', 'payment_status', 'payment_method', 'payment_type',
            'amount', 'balance_after', 'account_reference', 'receipt_url',
            'mpesa_details', 'bank_details', 'cash_details',
            'created_at', 'updated_at'
        ]

class PaymentWriteSerializer(serializers.ModelSerializer):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())
    payment_status = serializers.ChoiceField(choices=PaymentStatus.choices, source='status')
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, source='method')

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'property', 'tenant', 'unit', 'due_date',
            'paid_date', 'payment_status', 'payment_method', 'payment_type',
            'amount', 'balance_after', 'account_reference', 'receipt_url'
        ]
        read_only_fields = ['id', 'payment_id', 'balance_after']

    def validate(self, data):
        if data.get('paid_date') and data.get('due_date'):
            if data['paid_date'] < data['due_date']:
                raise serializers.ValidationError("Paid date cannot be earlier than due date")
        
        # Validate that unit belongs to the property
        if data.get('unit') and data.get('property'):
            if data['unit'].property_fk != data['property']:
                raise serializers.ValidationError("Unit must belong to the selected property")
        
        # Validate that tenant is assigned to the unit
        if data.get('tenant') and data.get('unit'):
            if data['unit'].current_tenant != data['tenant']:
                raise serializers.ValidationError("Tenant must be currently assigned to the unit")

        # Validate payment amount
        if data.get('amount'):
            if data['amount'] <= 0:
                raise serializers.ValidationError("Payment amount must be greater than zero")

        # Validate payment method specific fields
        method = data.get('method')
        if method == PaymentMethod.MPESA:
            if not data.get('account_reference'):
                raise serializers.ValidationError("Account reference is required for M-Pesa payments")
        
        return data

class PaymentReceiptReadSerializer(serializers.ModelSerializer):
    payment = PaymentReadSerializer()

    class Meta:
        model = PaymentReceipt
        fields = [
            'id', 'payment', 'receipt_number', 'issued_date',
            'file_url', 'created_at', 'updated_at'
        ]

class PaymentReceiptWriteSerializer(serializers.ModelSerializer):
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())

    class Meta:
        model = PaymentReceipt
        fields = ['id', 'payment', 'receipt_number', 'file_url']
        read_only_fields = ['id', 'receipt_number']


class InvoiceItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'amount', 'item_type']

class InvoiceItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'amount', 'item_type']
        read_only_fields = ['id']

class InvoiceReadSerializer(serializers.ModelSerializer):
    tenant = TenantReadSerializer()
    unit = UnitReadSerializer()
    items = InvoiceItemReadSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'tenant', 'unit', 'due_date',
            'amount', 'balance', 'late_fee', 'previous_balance',
            'status', 'items', 'total_amount', 'days_overdue',
            'created_at', 'updated_at'
        ]

    def get_total_amount(self, obj):
        return obj.amount + obj.late_fee

    def get_days_overdue(self, obj):
        if obj.status == 'OVERDUE':
            return (timezone.now() - obj.due_date).days
        return 0

class InvoiceWriteSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())
    items = InvoiceItemWriteSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'tenant', 'unit', 'due_date',
            'amount', 'balance', 'late_fee', 'previous_balance',
            'status', 'items'
        ]
        read_only_fields = ['id', 'invoice_number', 'balance', 'late_fee']

    def validate(self, data):
        # Validate that tenant is assigned to the unit
        if data.get('tenant') and data.get('unit'):
            if data['unit'].current_tenant != data['tenant']:
                raise serializers.ValidationError("Tenant must be currently assigned to the unit")

        # Validate due date is not in the past for new invoices
        if not self.instance and data.get('due_date'):
            if data['due_date'] < timezone.now():
                raise serializers.ValidationError("Due date cannot be in the past for new invoices")

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        # Send SMS notification
        try:
            from communications.services import SMSService
            sms_service = SMSService()
            
            # Format the due date
            due_date = validated_data['due_date'].strftime('%Y-%m-%d')
            
            # Get tenant's name and phone number
            tenant = validated_data['tenant']
            tenant_name = tenant.user.full_name if tenant.user else f"Tenant {tenant.tenant_id}"
            
            print(f"Debug - Tenant info: Name={tenant_name}, Phone={tenant.phone}")
            print(f"Debug - Invoice info: Number={invoice.invoice_number}, Amount={validated_data['amount']}, Due={due_date}")
            
            # Send SMS using the invoice_notification template
            result = sms_service.send_sms(
                recipients=[tenant.phone],
                message=sms_service.message_templates['invoice_notification'].format(
                    name=tenant_name,
                    amount=validated_data['amount'],
                    invoice_number=invoice.invoice_number,
                    due_date=due_date
                )
            )
            print(f"Debug - SMS sending result: {result}")
            
        except Exception as e:
            # Log the error but don't prevent invoice creation
            print(f"Debug - Failed to send SMS notification: {str(e)}")
            print(f"Debug - Full error: {repr(e)}")

        return invoice