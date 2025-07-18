# accounts/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.contrib.auth import login
from accounts.models import User
from accounts.permissions import IsLandlord, IsTenant
from accounts.serializers import UserReadSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
import logging
from rest_framework import generics, permissions
from rest_framework.response import Response
from .serializers import UserProfileSerializer, UserReadSerializer  # Add UserReadSerializer import
from rest_framework.decorators import api_view  # Add this import
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status 
from django.contrib.auth import login
# Remove or comment out this line:
# from .firebase_auth_backend import FirebaseAuthentication

# Add this line:
from .firebase_auth_backend import FirebaseAuthenticationBackend
logger = logging.getLogger(__name__)


class DebugAuthView(APIView):
    """
    Debug endpoint to check authentication and permissions.
    This view is public and doesn't require authentication.
    """
    permission_classes = []  # No permissions required
    
    def get(self, request):
        """
        Return information about the authenticated user and their permissions.
        """
        # Log request headers for debugging
        headers = {k: v for k, v in request.META.items()}
        logger.info("\n=== DebugAuthView ===")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request user: {request.user}")
        logger.info(f"User is authenticated: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'N/A'}")
        logger.info(f"Request headers: {headers}")
        
        # Get the raw Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '') 
        logger.info(f"Raw Authorization header: {auth_header}")
        
        # Get user from request
        user = request.user
        logger.info(f"DebugAuthView - Request user: {user}, is_authenticated: {getattr(user, 'is_authenticated', False)}")
        
        # Check if user is authenticated in the request
        if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            logger.warning("DebugAuthView - No authenticated user")
            return Response({
                'is_authenticated': False,
                'message': 'No authenticated user. Include a valid Firebase ID token in the Authorization header.'
            }, status=status.HTTP_200_OK)
        
        # Log detailed user information
        logger.info(f"DebugAuthView - User: {user.email}")
        logger.info(f"DebugAuthView - User ID: {user.id}")
        logger.info(f"DebugAuthView - Is Authenticated: {user.is_authenticated}")
        logger.info(f"DebugAuthView - Role: {getattr(user, 'role', 'no role')}")
        logger.info(f"DebugAuthView - Is Staff: {getattr(user, 'is_staff', False)}")
        logger.info(f"DebugAuthView - Is Superuser: {getattr(user, 'is_superuser', False)}")
        
        # Check if user has landlord permissions
        is_landlord = getattr(user, 'role', '') == 'landlord'
        logger.info(f"DebugAuthView - Is Landlord: {is_landlord}")
        
        # Get user groups and permissions
        groups = [] 
        permissions = []
        if hasattr(user, 'get_group_permissions'):
            permissions = list(user.get_group_permissions())
        if hasattr(user, 'groups') and hasattr(user.groups, 'all'):
            groups = [group.name for group in user.groups.all()]
        
        # Get all user attributes for debugging
        user_attrs = {}
        if user and hasattr(user, '__dict__'):
            user_attrs = {
                k: str(v) for k, v in user.__dict__.items() 
                if not k.startswith('_') and not k == 'password'
            }
        
        return Response({
            'email': user.email,
            'id': user.id,
            'is_authenticated': user.is_authenticated,
            'role': getattr(user, 'role', 'no role'),
            'is_staff': getattr(user, 'is_staff', False),
            'is_superuser': getattr(user, 'is_superuser', False),
            'has_landlord_permission': is_landlord,
            'groups': groups,
            'permissions': permissions,
            'auth_backend': str(user.backend) if hasattr(user, 'backend') else 'no backend',
            'user_attributes': user_attrs,
        })



class FirebaseLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            id_token = request.data.get('id_token')
            if not id_token:
                return Response({'error': 'No ID token provided'}, 
                               status=status.HTTP_400_BAD_REQUEST)

            firebase_auth = FirebaseAuthenticationBackend()
            user = firebase_auth.authenticate(request, token=id_token)
            
            if user:
                login(request, user, backend='accounts.firebase_auth_backend.FirebaseAuthenticationBackend')
                # Include user data in response
                return Response({
                    'message': 'Successfully logged in',
                    'user': {
                        'email': user.email,
                        'role': user.role,
                        'name': user.name if hasattr(user, 'name') else None
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid token'}, 
                               status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({'error': str(e)}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListUsersView(APIView):
    """
    List all users. Temporarily accessible by anyone.
    """
    permission_classes = [AllowAny]  # Temporarily allow any user to access

    def get(self, request):
        users = User.objects.all()
        serializer = UserReadSerializer(users, many=True)
        return Response(serializer.data)


class CreateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role", "tenant")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        phone = request.data.get("phone", "")

        # Basic validation
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate role
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if role not in valid_roles:
            return Response(
                {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user with email already exists in our database
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "A user with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Create or get Firebase user
            import firebase_admin
            from firebase_admin import auth, exceptions
            firebase_user = None
            try:
                firebase_user = auth.get_user_by_email(email)
                # Optionally update custom claims if needed
                auth.set_custom_user_claims(firebase_user.uid, {'role': role})
            except exceptions.NotFoundError:
                # User does not exist in Firebase, create them
                firebase_user = auth.create_user(
                    email=email,
                    email_verified=False,
                    password=password,
                    display_name=f"{first_name} {last_name}".strip(),
                    phone_number=phone if phone else None
                )
                # Set custom claims (including role)
                auth.set_custom_user_claims(
                    firebase_user.uid,
                    {'role': role}
                )
            except exceptions.FirebaseError as e:
                return Response(
                    {"error": f"Firebase error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 2. Create local Django user
            try:
                user = User.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    firebase_uid=firebase_user.uid,
                    phone=phone,
                    role=role,
                    is_active=True
                )
                # 3. Return success response
                serializer = UserReadSerializer(user)
                return Response({
                    "message": f"{role.title()} created successfully",
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Clean up Firebase user if it was created
                if firebase_user:
                    try:
                        auth.delete_user(firebase_user.uid)
                    except Exception as delete_error:
                        print(f"Error cleaning up Firebase user: {delete_error}")
                return Response(
                    {"error": f"An error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except exceptions.FirebaseError as e:
            return Response(
                {"error": f"Firebase error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    def put(self, request):
        """Update current user's profile"""
        serializer = UserWriteSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def firebase_login(request):
    id_token = request.data.get('id_token')
    try:
        user = User.objects.get(email=email)
        return Response({
            'status': 'success',
            'user': {
                'uid': decoded_token['uid'],
                'email': email,
                'role': user.role  # Ensure role is included
            }
        }, status=200)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=401)


@api_view(['GET'])
def check_session(request):
    if request.user.is_authenticated:
        return Response({'status': 'active'})
    return Response({'status': 'inactive'}, status=401)
