from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment

@receiver(pre_save, sender=Payment)
def generate_payment_id(sender, instance, **kwargs):
    if instance.payment_id == 'LEGACY-ID' or not instance.payment_id:
        # Format: PAY-{property_id}-{unit_id}-{tenant_id}-{timestamp}
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        instance.payment_id = f"PAY-P{instance.property_id}-U{instance.unit_id}-T{instance.tenant_id}-{timestamp}"