from django.core.management.base import BaseCommand
from accounts.models import User
import firebase_admin
from firebase_admin import auth as firebase_auth
import logging

class Command(BaseCommand):
    help = 'Sync all Django users to Firebase Auth (create or update)'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        synced = 0
        failed = 0
        for user in User.objects.filter(is_active=True, email__isnull=False).exclude(email=''):
            try:
                try:
                    firebase_user = firebase_auth.get_user_by_email(user.email)
                    update_args = {'password': '1234567'}  # Always set password
                    if firebase_user.display_name != (user.name or user.email):
                        update_args['display_name'] = user.name or user.email
                    custom_claims = firebase_user.custom_claims or {}
                    if custom_claims.get('role') != user.role:
                        custom_claims['role'] = user.role
                        update_args['custom_claims'] = custom_claims
                    firebase_auth.update_user(firebase_user.uid, **update_args)
                except firebase_auth.UserNotFoundError:
                    firebase_auth.create_user(
                        email=user.email,
                        display_name=user.name or user.email,
                        disabled=not user.is_active,
                        password='1234567',
                    )
                    # Set role claim
                    firebase_user = firebase_auth.get_user_by_email(user.email)
                    firebase_auth.set_custom_user_claims(firebase_user.uid, {'role': user.role})
                synced += 1
                self.stdout.write(self.style.SUCCESS(f"Synced: {user.email} ({user.role})"))
            except Exception as e:
                failed += 1
                logger.error(f"Failed to sync {user.email}: {e}")
                self.stdout.write(self.style.ERROR(f"Failed: {user.email} - {e}"))
        self.stdout.write(self.style.SUCCESS(f"\nDone. Synced: {synced}, Failed: {failed}"))
