from django.db import models
from landlords.models import Landlord


class Property(models.Model):
    """
    Represents a rental property owned by a landlord.
    Can contain multiple units (e.g., Apartment A, B, etc.)
    """
    landlord = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='properties'
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('under_construction', 'Under Construction')
        ],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('landlord', 'name')

    def __str__(self):
        return f"{self.name} ({self.landlord.business_name})"