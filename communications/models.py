from django.db import models
from landlords.models import Landlord
from tenants.models import Tenant


class SmsMessage(models.Model):
    """
    Represents an SMS message sent to one or more tenants.
    """
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    )

    landlord = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='sms_messages'
    )
    recipients = models.ManyToManyField(
        Tenant,
        related_name='received_sms'
    )
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='queued'
    )
    external_message_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SMS to {self.recipients.count()} tenant(s) - {self.status}"


class SmsTemplate(models.Model):
    """Represents a reusable SMS template"""
    name = models.CharField(max_length=100)
    content = models.TextField()
    landlord = models.ForeignKey(
        Landlord,
        on_delete=models.CASCADE,
        related_name='sms_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name