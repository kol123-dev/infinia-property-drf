from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from landlords.models import Landlord

class PropertyType(models.TextChoices):
    RESIDENTIAL = 'RESIDENTIAL', 'Residential'
    COMMERCIAL = 'COMMERCIAL', 'Commercial'
    MIXED_USE = 'MIXED_USE', 'Mixed Use'

class ResidentialType(models.TextChoices):
    APARTMENT = 'APARTMENT', 'Apartment'
    SINGLE_FAMILY = 'SINGLE_FAMILY', 'Single Family'
    TOWNHOUSE = 'TOWNHOUSE', 'Townhouse'

class BuildingType(models.TextChoices):
    STOREY = 'STOREY', 'Storey'
    GROUND_FLOOR = 'GROUND_FLOOR', 'Ground Floor'

class Property(models.Model):
    """Represents a rental property with detailed tracking of units, financials, and occupancy."""
    # Basic Information
    property_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    landlord = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='properties',
        null=True,
        blank=True
    )
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.SET_NULL,
        related_name='managed_properties',
        null=True,
        blank=True
    )
    address = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Property Classification
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.RESIDENTIAL
    )
    residential_type = models.CharField(
        max_length=20,
        choices=ResidentialType.choices,
        null=True,
        blank=True
    )
    building_type = models.CharField(
        max_length=20,
        choices=BuildingType.choices,
        default=BuildingType.STOREY
    )

    # Unit Statistics
    total_units = models.PositiveIntegerField(default=0)
    occupied_units = models.PositiveIntegerField(default=0)
    vacant_units = models.PositiveIntegerField(default=0)
    under_maintenance_units = models.PositiveIntegerField(default=0)

    # Financial Information
    potential_monthly_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    actual_monthly_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Auto-calculated Fields
    occupancy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)  # You might want to add choices for this

    class Meta:
        verbose_name_plural = 'Properties'
        unique_together = ('landlord', 'name')

    def save(self, *args, **kwargs):
        # Calculate occupancy rate before saving
        if self.total_units > 0:
            self.occupancy_rate = (self.occupied_units / self.total_units) * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.landlord.business_name})"

    def get_units_by_status(self, status):
        return self.units.filter(status=status).select_related('current_tenant')

    def get_units_by_type(self, unit_type):
        return self.units.filter(type=unit_type).select_related('current_tenant')

    def get_expiring_leases(self, days=30):
        threshold = timezone.now() + timezone.timedelta(days=days)
        return self.units.filter(
            Q(lease_end_date__lte=threshold) & 
            Q(status=UnitStatus.OCCUPIED)
        ).select_related('current_tenant')

    def get_vacant_units_summary(self):
        return self.units.filter(status=UnitStatus.VACANT).aggregate(
            count=Count('id'),
            total_potential_revenue=Sum('rent')
        )

    def get_unit_type_distribution(self):
        return self.units.values('type').annotate(
            count=Count('id'),
            occupied=Count('id', filter=Q(status=UnitStatus.OCCUPIED)),
            total_revenue=Sum('rent', filter=Q(status=UnitStatus.OCCUPIED))
        )

    def calculate_occupancy_metrics(self):
        if self.total_units > 0:
            return {
                'occupancy_rate': self.occupancy_rate,
                'vacancy_rate': (self.vacant_units / self.total_units) * 100,
                'maintenance_rate': (self.under_maintenance_units / self.total_units) * 100
            }
        return {'occupancy_rate': 0, 'vacancy_rate': 0, 'maintenance_rate': 0}

class UnitType(models.Model):
    """Tracks different unit types and their counts within a property."""
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='unit_types'
    )
    name = models.CharField(max_length=50)  # e.g., "2BR/2BA/OK"
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('property', 'name')

class RevenueHistory(models.Model):
    """Tracks monthly revenue history for properties."""
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='revenue_history'
    )
    month = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('property', 'month')
        ordering = ['-month']