from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q

class UnitType(models.TextChoices):
    TWO_BED_TWO_BATH_OK = '2BR/2BA/OK', '2 Bedroom 2 Bathroom Open Kitchen'
    TWO_BED_THREE_BATH_CK = '2BR/3BA/CK', '2 Bedroom 3 Bathroom Closed Kitchen'

class UnitStatus(models.TextChoices):
    OCCUPIED = 'OCCUPIED', 'Occupied'
    VACANT = 'VACANT', 'Vacant'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'

class Unit(models.Model):
    # Identification
    unit_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    unit_number = models.CharField(max_length=20, default='TBD')
    property_fk = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='units'
    )

    # Unit Details
    type = models.CharField(
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.TWO_BED_TWO_BATH_OK
    )
    status = models.CharField(
        max_length=20,
        choices=UnitStatus.choices,
        default=UnitStatus.VACANT
    )
    floor = models.PositiveIntegerField(null=True, blank=True)
    size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )

    # Financial
    rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )

    # Features
    amenities = models.JSONField(
        default=list,
        help_text='List of amenities ["balcony", "parking", etc]'
    )
    features = models.JSONField(
        default=dict,
        help_text='Additional unit features {"parking_spots": 2, "storage_unit": "B12"}'
    )

    # Occupancy
    current_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unit_tenant'
    )
    lease_start_date = models.DateTimeField(null=True, blank=True)
    lease_end_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('property_fk', 'unit_number')]
        indexes = [
            models.Index(fields=['property_fk', 'status']),
            models.Index(fields=['property_fk', 'type']),
            models.Index(fields=['current_tenant']),
            models.Index(fields=['lease_end_date'])
        ]
        ordering = ['property_fk', 'unit_number']

    @classmethod
    def bulk_create_units(cls, property_instance, units_data):
        units = [cls(**{**data, 'property_fk': property_instance}) for data in units_data]
        return cls.objects.bulk_create(units)

    def __str__(self):
        return f"{self.unit_number} - {self.property_fk.name}"

    def assign_tenant(self, tenant, lease_start_date=None, lease_end_date=None):
        """Assign a tenant to this unit and create history record."""
        from django.utils import timezone
        
        # If there's a current tenant, end their tenancy
        if self.current_tenant:
            self.end_tenancy()
        
        # Update unit
        self.current_tenant = tenant
        self.status = UnitStatus.OCCUPIED
        self.lease_start_date = lease_start_date or timezone.now()
        self.lease_end_date = lease_end_date
        self.save()
        
        # Update tenant's unit reference
        tenant.current_unit = self
        tenant.status = 'ACTIVE'
        tenant.move_in_date = self.lease_start_date
        tenant.save()
        
        # Create history record
        UnitTenantHistory.objects.create(
            unit=self,
            tenant=tenant,
            start_date=self.lease_start_date,
            end_date=self.lease_end_date
        )

    def end_tenancy(self, end_date=None):
        """End current tenancy and update history."""
        from django.utils import timezone
        
        if not self.current_tenant:
            return
            
        end_date = end_date or timezone.now()
        
        # Update history record
        history = UnitTenantHistory.objects.filter(
            unit=self,
            tenant=self.current_tenant,
            end_date__isnull=True
        ).first()
        
        if history:
            history.end_date = end_date
            history.save()
        
        # Update tenant
        tenant = self.current_tenant
        tenant.current_unit = None
        tenant.status = 'PAST'
        tenant.move_out_date = end_date
        tenant.save()
        
        # Update unit
        self.current_tenant = None
        self.status = UnitStatus.VACANT
        self.lease_start_date = None
        self.lease_end_date = None
        self.save()

    # Property methods
    @property
    def check_occupancy_status(self):
        return self.status == UnitStatus.OCCUPIED

    @property
    def check_vacancy_status(self):
        return self.status == UnitStatus.VACANT

    @property
    def check_maintenance_status(self):
        return self.status == UnitStatus.MAINTENANCE

    @property
    def check_lease_status(self):
        from django.utils import timezone
        return bool(
            self.lease_start_date and 
            self.lease_end_date and 
            self.lease_start_date <= timezone.now() <= self.lease_end_date
        )

class UnitTenantHistory(models.Model):
    """Tracks the history of tenants for each unit."""
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tenant_history')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def get_tenant_history(self):
        """Get complete tenant history for this unit."""
        return self.tenant_history.all().select_related('tenant').order_by('-start_date')