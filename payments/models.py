from django.db import models
from landlords.models import Landlord
from tenants.models import Tenant
from units.models import Unit


class Payment(models.Model):
    """
    Represents a rent payment made by a tenant.
    """
    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    landlord = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_code = models.CharField(max_length=100, unique=True)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.tenant.name}"


class PaymentReceipt(models.Model):
    """
    Represents a receipt issued after successful payment.
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='receipt'
    )
    receipt_number = models.CharField(max_length=100, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('sent', 'Sent'), ('draft', 'Draft')],
        default='draft'
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number} for {self.payment}"