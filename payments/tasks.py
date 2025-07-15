from celery import shared_task, Task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import models
import decimal  # Add this import for late fee calculation
from .models import Invoice, InvoiceItem
from tenants.models import Tenant
from .serializers import InvoiceWriteSerializer
import logging

logger = logging.getLogger(__name__)

class NoOverrideTask(Task):
    """Custom task class that prevents function overrides"""
    abstract = True

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

@shared_task(bind=True, base=NoOverrideTask)
def generate_monthly_invoices(self):
    """Generate monthly invoices for all active tenants"""
    now = timezone.now()
    due_date = now + timezone.timedelta(days=5)  # Set due date 5 days in future

    # Get active tenants with units
    active_tenants = Tenant.objects.filter(
        status='ACTIVE',
        current_unit__isnull=False
    ).select_related('current_unit')
    
    logger.info(f"Found {active_tenants.count()} active tenants with units")
    
    invoices_created = 0
    for tenant in active_tenants:
        try:
            # Check if an invoice already exists for this month
            existing_invoice = Invoice.objects.filter(
                tenant=tenant,
                created_at__month=now.month,
                created_at__year=now.year
            ).first()
            
            if existing_invoice:
                logger.info(f"Invoice already exists for tenant {tenant.id} for {now.month}/{now.year}")
                continue

            # Verify tenant is assigned to the unit
            if not tenant.current_unit or tenant.current_unit.current_tenant != tenant:
                logger.error(f"Tenant {tenant.id} is not properly assigned to unit {tenant.current_unit.id if tenant.current_unit else 'None'}")
                continue

            # Create invoice data
            invoice_data = {
                'tenant': tenant.id,
                'unit': tenant.current_unit.id,
                'due_date': due_date.isoformat(),
                'amount': tenant.current_unit.rent,
                'status': 'SENT',  # Set status to SENT immediately
                'items': [
                    {
                        'description': 'Monthly Rent',
                        'amount': tenant.current_unit.rent,
                        'item_type': 'RENT'
                    }
                ]
            }

            # Create new invoice using serializer
            serializer = InvoiceWriteSerializer(data=invoice_data)
            if serializer.is_valid():
                new_invoice = serializer.save()
                invoices_created += 1
                logger.info(f"Created invoice {new_invoice.invoice_number} for tenant {tenant.id}")
            else:
                logger.error(f"Failed to create invoice for tenant {tenant.id}: {serializer.errors}")

        except Exception as e:
            logger.error(f"Error processing tenant {tenant.id}: {str(e)}")
            continue
    
    logger.info(f"Total invoices created: {invoices_created}")
    return invoices_created

@shared_task(base=NoOverrideTask)
def check_overdue_invoices():
    """Check for overdue invoices and apply late fees"""
    overdue_invoices = Invoice.objects.filter(
        status__in=['SENT', 'OVERDUE'],
        due_date__lt=timezone.now(),
        late_fee_applied=False
    )

    for invoice in overdue_invoices:
        invoice.status = 'OVERDUE'
        invoice.calculate_late_fee()