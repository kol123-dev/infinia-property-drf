from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from tenants.models import Tenant, TenantStatus  # Add TenantStatus
from payments.models import (
    Payment, PaymentReceipt, MpesaTransaction,
    BankTransaction, CashPayment, Invoice, InvoiceItem  # Add Invoice and InvoiceItem
)
from payments.serializers import (
    PaymentReadSerializer, PaymentWriteSerializer,
    PaymentReceiptReadSerializer, PaymentReceiptWriteSerializer,
    MpesaTransactionReadSerializer, MpesaTransactionWriteSerializer,
    BankTransactionReadSerializer, BankTransactionWriteSerializer,
    CashPaymentReadSerializer, CashPaymentWriteSerializer,
    InvoiceReadSerializer, InvoiceWriteSerializer  # Add these imports
)
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter

class InvoiceFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    status = filters.ChoiceFilter(choices=Invoice.status.field.choices)
    due_date_from = filters.DateTimeFilter(field_name="due_date", lookup_expr='gte')
    due_date_to = filters.DateTimeFilter(field_name="due_date", lookup_expr='lte')

    class Meta:
        model = Invoice
        fields = ['tenant', 'unit', 'status']

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InvoiceFilter
    search_fields = ['invoice_number', 'tenant__name', 'unit__unit_number']
    ordering_fields = ['due_date', 'amount', 'created_at']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return InvoiceReadSerializer
        return InvoiceWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add any custom filtering logic here
        return queryset

    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = 'PAID'
        invoice.save()
        return Response({'status': 'Invoice marked as paid'})

    @action(detail=True, methods=['post'])
    def apply_late_fee(self, request, pk=None):
        invoice = self.get_object()
        invoice.calculate_late_fee()
        return Response({
            'status': 'Late fee applied',
            'late_fee': invoice.late_fee,
            'new_balance': invoice.balance
        })

    @action(detail=False, methods=['post'])
    def generate_bulk_invoices(self, request):
        from .tasks import generate_monthly_invoices
        task = generate_monthly_invoices.delay()
        return Response({
            'status': 'Task started',
            'task_id': task.id
        })

    @action(detail=False, methods=['get'])
    def check_generation_status(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'error': 'task_id is required'}, status=400)

        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)
        
        return Response({
            'status': task_result.status,
            'result': task_result.result if task_result.ready() else None
        })

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PaymentReadSerializer
        return PaymentWriteSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.select_related(
            'property', 'property__landlord', 'property__agent',
            'tenant', 'tenant__user',
            'unit', 'unit__property_fk'
        )
        
        # Role-based filtering
        if user.role == 'landlord':
            # Landlords can see payments for their properties
            queryset = queryset.filter(property__landlord__user=user)
        elif user.role == 'agent':
            # Agents can see payments for properties they manage
            queryset = queryset.filter(property__agent__user=user)
        elif user.role == 'tenant':
            # Tenants can only see their own payments
            queryset = queryset.filter(tenant__user=user)
        
        # Additional filters
        property_id = self.request.query_params.get('property')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
            
        tenant_id = self.request.query_params.get('tenant')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
            
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
            
        return queryset

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        payment = self.get_object()
        payment.status = 'PAID'
        payment.save()
        return Response({'status': 'payment confirmed'})

class PaymentReceiptViewSet(viewsets.ModelViewSet):
    queryset = PaymentReceipt.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PaymentReceiptReadSerializer
        return PaymentReceiptWriteSerializer

class MpesaTransactionViewSet(viewsets.ModelViewSet):
    queryset = MpesaTransaction.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return MpesaTransactionReadSerializer
        return MpesaTransactionWriteSerializer

    @action(detail=False, methods=['post'])
    def callback(self, request):
        try:
            # Get unit number from account reference
            unit_number = request.data.get('account_reference')  # e.g., 'A207'
            phone_number = request.data.get('phone_number')
            
            # Find tenant by unit and phone - Fixed status field name
            tenant = Tenant.objects.filter(
                current_unit__unit_number=unit_number,
                phone=phone_number,
                status=TenantStatus.ACTIVE  # Changed from tenant_status to status
            ).first()
            
            # Create payment record first (even for unmatched cases)
            payment = Payment.objects.create(
                payment_id=f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                property=tenant.current_unit.property_fk if tenant else None,
                tenant=tenant,
                unit=tenant.current_unit if tenant else None,
                paid_date=timezone.now(),
                status='PAID' if tenant else 'PENDING',
                method='MPESA',
                payment_type='RENT',
                amount=request.data.get('amount'),
                account_reference=unit_number
            )
            
            # Then create transaction record with payment linked
            transaction = MpesaTransaction.objects.create(
                payment=payment,
                transaction_id=request.data.get('transaction_id'),
                phone_number=phone_number,
                amount=request.data.get('amount'),
                paybill_number=request.data.get('paybill_number'),
                account_reference=unit_number,
                transaction_date=timezone.now(),
                status='COMPLETED' if tenant else 'UNMATCHED',
                result_code=request.data.get('result_code'),
                result_description='Success' if tenant else 'Tenant not found for unit and phone combination'
            )
            
            return Response({'status': 'success' if tenant else 'pending_review'})
            
        except Exception as e:
            # Create payment first for error case
            payment = Payment.objects.create(
                payment_id=f"PAY-ERROR-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                status='PENDING',
                method='MPESA',
                payment_type='RENT',
                amount=request.data.get('amount'),
                account_reference=request.data.get('account_reference')
            )
            
            # Then create transaction with payment linked
            transaction = MpesaTransaction.objects.create(
                payment=payment,
                transaction_id=request.data.get('transaction_id'),
                phone_number=request.data.get('phone_number'),
                amount=request.data.get('amount'),
                paybill_number=request.data.get('paybill_number'),
                account_reference=request.data.get('account_reference'),
                transaction_date=timezone.now(),
                status='ERROR',
                result_code='ERROR',
                result_description=str(e)
            )
            return Response({'status': 'error', 'message': str(e)}, status=500)

class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return BankTransactionReadSerializer
        return BankTransactionWriteSerializer

    @action(detail=False, methods=['post'])
    def ipn_callback(self, request):
        # Handle bank IPN callback
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save()
            # Update related payment if verified
            if transaction.verification_status == 'VERIFIED':
                payment = transaction.payment
                payment.status = 'PAID'
                payment.paid_date = transaction.transfer_date
                payment.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CashPaymentViewSet(viewsets.ModelViewSet):
    queryset = CashPayment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CashPaymentReadSerializer
        return CashPaymentWriteSerializer

    def perform_create(self, serializer):
        cash_payment = serializer.save(received_by=self.request.user)
        # Update related payment
        payment = cash_payment.payment
        payment.status = 'PAID'
        payment.paid_date = cash_payment.created_at
        payment.save()