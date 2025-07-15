from django.db import models
from django.core.validators import MinValueValidator
from properties.models import Property
from units.models import Unit
from tenants.models import Tenant

class RenewalStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    EXPIRED = 'EXPIRED', 'Expired'
    RENEWED = 'RENEWED', 'Renewed'

class Lease(models.Model):
    """Represents a lease agreement with detailed terms and tracking."""
    lease_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    rent_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    
    # Deposit information
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    
    # Lease terms
    document_url = models.URLField(null=True, blank=True)
    terms = models.JSONField(default=dict)  # Store as {"utilitiesIncluded": true, "petsAllowed": false, ...}
    renewal_status = models.CharField(
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.ACTIVE
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']