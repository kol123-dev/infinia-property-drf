from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from landlords.models import Landlord

@receiver(post_save, sender=User)
def sync_firebase_user(sender, instance, created, **kwargs):
    """
    Ensure every User is synced to Firebase Auth (create or update).
    """
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    import logging
    logger = logging.getLogger(__name__)

    if not instance.email or not instance.is_active:
        return
    try:
        try:
            firebase_user = firebase_auth.get_user_by_email(instance.email)
            # Update display name and custom claims if needed
            update_args = {}
            if firebase_user.display_name != (instance.name or instance.email):
                update_args['display_name'] = instance.name or instance.email
            custom_claims = firebase_user.custom_claims or {}
            if custom_claims.get('role') != instance.role:
                custom_claims['role'] = instance.role
                update_args['custom_claims'] = custom_claims
            if update_args:
                firebase_auth.update_user(firebase_user.uid, **update_args)
        except firebase_auth.UserNotFoundError:
            firebase_auth.create_user(
                email=instance.email,
                display_name=instance.name or instance.email,
                disabled=not instance.is_active,
            )
            # Set role claim
            firebase_user = firebase_auth.get_user_by_email(instance.email)
            firebase_auth.set_custom_user_claims(firebase_user.uid, {'role': instance.role})
    except Exception as e:
        logger.error(f"Error syncing user to Firebase: {e}")

@receiver(post_save, sender=User)
def sync_landlord_profile(sender, instance, created, **kwargs):
    if instance.role == 'landlord':
        landlord, _ = Landlord.objects.get_or_create(user=instance, defaults={
            'business_name': instance.name or instance.email,
            'phone': instance.phone,
            'is_active': instance.is_active,
        })
        # Keep fields in sync
        landlord.business_name = instance.name or instance.email
        landlord.phone = instance.phone
        landlord.is_active = instance.is_active
        landlord.save()
    else:
        # If the user is no longer a landlord, delete the landlord profile if it exists
        Landlord.objects.filter(user=instance).delete()
