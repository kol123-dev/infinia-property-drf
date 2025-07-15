from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone  # Add this import
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
    LATE = 'LATE', 'Late'
    PARTIAL = 'PARTIAL', 'Partial'

class PaymentMethod(models.TextChoices):
    MPESA = 'MPESA', 'M-Pesa'
    BANK = 'BANK', 'Bank Transfer'
    CASH = 'CASH', 'Cash'

class Payment(models.Model):
    """Represents a payment with detailed tracking and status."""
    payment_id = models.CharField(max_length=50, unique=True, default=None)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='payments', null=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='payments', null=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='payments', null=True)
    due_date = models.DateTimeField(null=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MPESA
    )
    payment_type = models.CharField(
        max_length=20,
        choices=[
            ('RENT', 'Rent Payment'),
            ('DEPOSIT', 'Deposit'),
            ('UTILITY', 'Utility Payment'),
        ],
        default='RENT'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    account_reference = models.CharField(max_length=100, default=None)
    receipt_url = models.URLField(null=True, blank=True)  # Firebase Storage path
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date']

    def calculate_balance(self):
        """Calculate remaining balance after this payment"""
        # Get all unpaid invoices for this tenant
        unpaid_invoices = Invoice.objects.filter(
            tenant=self.tenant,
            status__in=['SENT', 'OVERDUE', 'PARTIALLY_PAID']
        )
        total_due = sum(invoice.balance for invoice in unpaid_invoices)
        return total_due - self.amount

    def save(self, *args, **kwargs):
        # Calculate balance before saving
        self.balance_after = self.calculate_balance()
        
        # Update payment status
        self.update_status()
        
        super().save(*args, **kwargs)

    def update_status(self):
        """Update payment status based on amount and due date"""
        if self.paid_date:
            if self.balance_after > 0:
                self.status = PaymentStatus.PARTIAL
            else:
                self.status = PaymentStatus.PAID
        elif self.due_date and self.due_date < timezone.now():
            self.status = PaymentStatus.LATE

class MpesaTransaction(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='mpesa_details')
    transaction_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paybill_number = models.CharField(max_length=20)
    account_reference = models.CharField(max_length=100)
    transaction_date = models.DateTimeField()
    status = models.CharField(max_length=20)
    result_code = models.CharField(max_length=20)
    result_description = models.TextField()

class BankTransaction(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='bank_details')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100)
    transfer_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    verification_status = models.CharField(max_length=20)
    ipn_response = models.JSONField(null=True, blank=True)

class CashPayment(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='cash_details')
    received_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_number = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)

class PaymentReceipt(models.Model):
    """Represents a receipt for a payment transaction."""
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='receipt'
    )
    receipt_number = models.CharField(max_length=50, unique=True, default='LEGACY-RECEIPT')
    issued_date = models.DateTimeField(auto_now_add=True)
    file_url = models.URLField(null=True, blank=True)  # Firebase Storage path for PDF/image
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number} for {self.payment.payment_id}"


class Invoice(models.Model):
    """Represents an invoice for rent or other charges"""
    invoice_number = models.CharField(max_length=50, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='invoices')
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    due_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee_applied = models.BooleanField(default=False)
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('SENT', 'Sent'),
            ('OVERDUE', 'Overdue'),
            ('PARTIALLY_PAID', 'Partially Paid'),
            ('PAID', 'Paid'),
            ('CANCELLED', 'Cancelled')
        ],
        default='DRAFT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_late_fee(self):
        """Calculate late fee if payment is overdue"""
        if not self.late_fee_applied and self.status in ['SENT', 'OVERDUE'] and timezone.now() > self.due_date:
            # Example: 10% late fee
            self.late_fee = self.balance * decimal.Decimal('0.10')
            self.late_fee_applied = True
            self.balance += self.late_fee
            self.save()

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMM-XXXX
            prefix = f"INV-{timezone.now().strftime('%Y%m')}-"
            last_invoice = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = str(last_number + 1).zfill(4)
            else:
                new_number = '0001'
            self.invoice_number = f"{prefix}{new_number}"

        if not self.balance:
            self.balance = self.amount

        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    """Individual items in an invoice"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item_type = models.CharField(
        max_length=20,
        choices=[
            ('RENT', 'Rent'),
            ('UTILITY', 'Utility'),
            ('DEPOSIT', 'Deposit'),
            ('PENALTY', 'Late Payment Penalty'),
            ('OTHER', 'Other Charges')
        ]
    )