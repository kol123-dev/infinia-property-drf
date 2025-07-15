from django.db import models
from accounts.models import User
from properties.models import Property

class PropertyManager(models.Model):
    """Represents a property manager/caretaker."""
    manager_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='property_manager_profile',
        limit_choices_to={'role': 'property_manager'}
    )
    
    # Work Details
    assigned_properties = models.ManyToManyField(
        Property,
        related_name='caretakers'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    shift_hours = models.JSONField(default=dict, help_text='Working hours schedule')
    
    # Contact Information
    emergency_phone = models.CharField(max_length=20, help_text='For after-hours emergencies', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Documents
    contract_url = models.URLField(null=True, blank=True)
    id_document_url = models.URLField(null=True, blank=True)
    
    # Status and Metadata
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.manager_id}"

    class Meta:
        ordering = ['-created_at']
