# accounts/firebase_auth_backend.py
import firebase_admin
from firebase_admin import auth as firebase_auth
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

User = get_user_model()

class FirebaseAuthenticationBackend(BaseBackend):
    """
    Custom authentication backend that uses Firebase for authentication.
    """
    
    def authenticate(self, request, token=None):
        """
        Authenticate a user using Firebase ID token.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not token:
            logger.warning("No token provided for authentication")
            return None

        try:
            logger.info(f"Starting authentication with token: {token[:20]}...")
            
            # 1. Verify Firebase ID token
            decoded_token = firebase_admin.auth.verify_id_token(token)
            logger.info(f"Token verified. UID: {decoded_token.get('uid')}, Email: {decoded_token.get('email')}")
            
            firebase_uid = decoded_token['uid']
            
            try:
                # 2. Try to find existing user by Firebase UID
                user = User.objects.get(firebase_uid=firebase_uid)
                logger.info(f"Found existing user: {user.email}, Role: {user.role}")
                return user
                
            except User.DoesNotExist:
                logger.info("User not found in local DB, checking Firebase...")
                # 3. If not found, fetch from Firebase and create local user
                firebase_user = firebase_admin.auth.get_user(firebase_uid)
                logger.info(f"Fetched Firebase user: {firebase_user.uid}, Email: {firebase_user.email}")
                
                email = firebase_user.email
                if not email:
                    logger.error("Firebase user has no email")
                    return None
                    
                name = firebase_user.display_name or email.split('@')[0]
                
                # Get custom claims if they exist
                custom_claims = firebase_user.custom_claims or {}
                role = custom_claims.get('role', 'tenant')  # Default to 'tenant' if no role claim
                logger.info(f"Creating new user with role: {role}")

                # Create the user
                user = User.objects.create(
                    email=email,
                    name=name,
                    firebase_uid=firebase_uid,
                    role=role,
                    is_active=True
                )
                logger.info(f"Created new user: {user.email} with role: {user.role}")
                return user

        except firebase_admin.exceptions.FirebaseError as e:
            logger.error(f"Firebase auth error: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}", exc_info=True)
            return None
    
    def get_user(self, user_id):
        """
        Get a user by their ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None