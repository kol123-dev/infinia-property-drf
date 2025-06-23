from django.db import models
from landlords.models import Landlord
from units.models import Unit
from accounts.models import User


class Tenant(models.Model):
    """
    Represents a rental tenant.
    Can be assigned to a unit.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('vacated', 'Vacated'),
        ('deposit_defaulter', 'Deposit Defaulter'),
        ('in_arrears', 'In Arrears'),
    )

    landlord = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='tenants'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'tenant'}
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='occupants'
    )
    move_in_date = models.DateField(null=True)
    expected_move_out_date = models.DateField(null=True, blank=True)
    actual_move_out_date = models.DateField(null=True, blank=True)
    arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name if self.user and hasattr(self.user, 'name') else self.user.email} - {self.landlord.business_name}"


class Contract(models.Model):
    """
    Represents a signed tenancy agreement.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    file = models.FileField(upload_to='contracts/', null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contract for {self.tenant.name} ({self.start_date} - {self.end_date})"