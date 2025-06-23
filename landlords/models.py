# landlords/models.py
from django.db import models
from accounts.models import User


class Landlord(models.Model):
    """
    Represents a landlord/organization in the SaaS platform.
    Acts as the multi-tenant root for scoping data.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='landlord_profile',
        limit_choices_to={'role': 'landlord'}
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_landlords',
        limit_choices_to={'role': 'agent'},
        help_text='The agent responsible for this landlord.'
    )
    business_name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    company_registration_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name