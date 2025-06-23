from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.conf import settings
import firebase_admin
from firebase_admin import auth as firebase_auth
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class FirebaseDRFAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class that authenticates users with a Firebase ID token.
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        id_token = auth_header.split('Bearer ')[-1].strip()
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            raise AuthenticationFailed(_('Invalid Firebase token: %(error)s') % {'error': str(e)})

        uid = decoded_token.get('uid')
        if not uid:
            raise AuthenticationFailed(_('No Firebase UID in token'))

        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            email = decoded_token.get('email')
            name = decoded_token.get('name', '')
            if not email:
                raise AuthenticationFailed(_('No email found in Firebase token'))
            # Try to find user by email and update firebase_uid if found
            try:
                user = User.objects.get(email=email)
                user.firebase_uid = uid
                user.save()
            except User.DoesNotExist:
                user = User.objects.create(
                    firebase_uid=uid,
                    email=email,
                    name=name,
                    role='agent'  # Default role, adjust as needed
                )
        # Optionally attach the token/decoded claims to the user or request
        request.firebase_claims = decoded_token
        return (user, None)
