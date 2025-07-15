from django.db import models
from django.db.models import Sum
from accounts.models import User

class Landlord(models.Model):
    """Represents a landlord/organization in the system."""
    landlord_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='landlord_profile',
        limit_choices_to={'role': 'landlord'}
    )
    
    # Basic Info
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    id_number = models.CharField(max_length=100, help_text='Encrypted', null=True, blank=True)
    
    # Business Details
    business_name = models.CharField(max_length=255, unique=True)
    company_registration_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Relationships - Using string reference to avoid circular import
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_landlords'
    )
    
    # Tax Information
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    tax_filing_status = models.BooleanField(default=False)
    last_tax_filing_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name

    @property
    def total_units(self):
        return self.properties.aggregate(total=Sum('units'))['total'] or 0

    @property
    def monthly_revenue(self):
        return self.properties.aggregate(
            revenue=Sum('units__rent_amount')
        )['revenue'] or 0