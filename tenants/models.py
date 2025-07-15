from django.db import models
from django.core.validators import MinValueValidator
from landlords.models import Landlord
from accounts.models import User

class TenantStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    PAST = 'PAST', 'Past'
    EVICTED = 'EVICTED', 'Evicted'
    APPLICANT = 'APPLICANT', 'Applicant'

class EmergencyContact(models.Model):
    """Represents an emergency contact for a tenant."""
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, related_name='emergency_contact')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50)

class Tenant(models.Model):
    """Represents a rental tenant with detailed tracking."""
    tenant_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='tenants', null=True, blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'tenant'}
    )
    
    # Basic Info
    phone = models.CharField(max_length=20, help_text='Formatted: "+1234567890"', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True, help_text='For lease compliance')
    
    # Lease/Living Details
    current_unit = models.OneToOneField(
        'units.Unit',  # Use string reference instead
        on_delete=models.SET_NULL,
        null=True,
        related_name='tenant_unit'  # Change related_name to avoid conflict
    )
    active_lease = models.OneToOneField(
        'lease.Lease',  # Use string reference instead of direct import
        on_delete=models.SET_NULL,
        null=True,
        related_name='current_tenant'
    )
    move_in_date = models.DateField(null=True, blank=True)
    move_out_date = models.DateField(null=True, blank=True)
    rent_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    payment_due_day = models.IntegerField(null=True, blank=True)
    
    # Financials
    balance_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Documents
    lease_agreement_url = models.URLField(null=True, blank=True)
    id_verification_url = models.URLField(null=True, blank=True)
    proof_of_income_url = models.URLField(null=True, blank=True)
    
    # Status and Metadata
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.APPLICANT
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name if self.user else self.tenant_id} - {self.current_unit}"

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