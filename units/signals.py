from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import Unit, UnitStatus

@receiver([post_save, post_delete], sender=Unit)
def update_property_statistics(sender, instance, **kwargs):
    property = instance.property_fk  # Changed from property to property_fk
    
    # Use annotate and aggregate for efficient querying
    stats = property.units.aggregate(
        total_units=models.Count('id'),
        occupied_units=models.Count('id', filter=models.Q(status=UnitStatus.OCCUPIED)),
        vacant_units=models.Count('id', filter=models.Q(status=UnitStatus.VACANT)),
        under_maintenance_units=models.Count('id', filter=models.Q(status=UnitStatus.MAINTENANCE)),
        potential_revenue=models.Sum('rent'),
        actual_revenue=models.Sum('rent', filter=models.Q(status=UnitStatus.OCCUPIED))
    )
    
    # Update property fields
    for field, value in stats.items():
        setattr(property, field, value or 0)
    
    # Calculate occupancy rate
    if stats['total_units']:
        property.occupancy_rate = (stats['occupied_units'] / stats['total_units']) * 100
    else:
        property.occupancy_rate = 0
    
    property.save()