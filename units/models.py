from django.db import models
from properties.models import Property


class Unit(models.Model):
    """
    Represents a single rental unit within a property.
    Can be assigned to a tenant.
    """
    UNIT_TYPE_CHOICES = (
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('garage', 'Garage'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='units'
    )
    unit_name = models.CharField(max_length=100)  # e.g., "Unit 1A"
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='residential')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vacant')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('property', 'unit_name')

    def __str__(self):
        return f"{self.unit_name} - {self.property.name}"