from django.db import models
from accounts.models import User
from properties.models import Property

class Agent(models.Model):
    """Represents a real estate agent or property management company."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        limit_choices_to={'role': 'agent'}
    )
    registration_number = models.CharField(max_length=100, unique=True, help_text='CR12 or business ID', null=True, blank=True)
    tax_id = models.CharField(max_length=100, unique=True, help_text='Encrypted tax identification', null=True, blank=True)
    
    # Address fields
    street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Additional contact numbers (stored as JSON array)
    additional_contacts = models.JSONField(default=list, help_text='Array of additional phone numbers')
    
    # Relationships - No need to import Landlord, it will be handled by reverse relation
    properties = models.ManyToManyField(Property, related_name='managing_agents')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.full_name or self.user.email

    @property
    def name(self):
        return self.user.full_name

    @property
    def email(self):
        return self.user.email

    @property
    def primary_contact(self):
        return self.user.phone
