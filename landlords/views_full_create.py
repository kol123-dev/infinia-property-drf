
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from firebase_admin import auth as firebase_auth
from accounts.models import User
from landlords.models import Landlord
from landlords.serializers import LandlordReadSerializer
from rental_backend.permissions import IsAgent
from rest_framework.permissions import IsAuthenticated
from tenants.models import Tenant
from tenants.serializers import TenantReadSerializer

class CreateFullLandlordView(APIView):
    permission_classes = [IsAgent, IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        business_name = data.get('business_name')
        phone = data.get('phone')
        address = data.get('address')
        company_registration_number = data.get('company_registration_number')

        if not email or not password or not business_name:
            return Response({'detail': 'Email, password, and business_name are required.'}, status=400)

        # 1. Create user in Firebase
        try:
            firebase_user = firebase_auth.create_user(email=email, password=password, display_name=name)
            firebase_uid = firebase_user.uid
        except Exception as e:
            return Response({'detail': f'Firebase user creation failed: {str(e)}'}, status=400)

        # 2. Create Django user (or update if exists)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'firebase_uid': firebase_uid,
                'name': name,
                'role': 'landlord',
                'is_active': True,
            }
        )
        if not created:
            user.firebase_uid = firebase_uid
            user.name = name
            user.role = 'landlord'
            user.is_active = True
            user.save()

        # 3. Create Landlord profile
        agent = request.user
        landlord = Landlord.objects.create(
            user=user,
            agent=agent,
            business_name=business_name,
            phone=phone,
            address=address,
            company_registration_number=company_registration_number,
            is_active=True
        )

        return Response(LandlordReadSerializer(landlord).data, status=status.HTTP_201_CREATED)

class CreateFullTenantView(APIView):
    permission_classes = [IsAgent, IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        phone = data.get('phone')
        landlord_id = data.get('landlord')
        unit_id = data.get('unit')
        if not email or not password or not name or not landlord_id:
            return Response({'detail': 'Email, password, name, and landlord are required.'}, status=400)

        # 1. Create user in Firebase
        try:
            firebase_user = firebase_auth.create_user(email=email, password=password, display_name=name)
            firebase_uid = firebase_user.uid
        except Exception as e:
            return Response({'detail': f'Firebase user creation failed: {str(e)}'}, status=400)

        # 2. Create Django user (or update if exists)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'firebase_uid': firebase_uid,
                'name': name,
                'role': 'tenant',
                'is_active': True,
            }
        )
        if not created:
            user.firebase_uid = firebase_uid
            user.name = name
            user.role = 'tenant'
            user.is_active = True
            user.save()

        # 3. Get landlord
        try:
            landlord = Landlord.objects.get(id=landlord_id)
        except Landlord.DoesNotExist:
            return Response({'detail': 'Landlord not found.'}, status=404)

        # 4. Create Tenant profile
        tenant = Tenant.objects.create(
            user=user,
            landlord=landlord,
            name=name,
            phone=phone,
            email=email,
            unit_id=unit_id if unit_id else None
        )

        return Response(TenantReadSerializer(tenant).data, status=status.HTTP_201_CREATED)

# --- PROPERTY MANAGER FULL CREATE ---
# If you have a property manager model, implement similarly. Here is a template:
try:
    from property_managers.models import PropertyManager
    from property_managers.serializers import PropertyManagerReadSerializer
except ImportError:
    PropertyManager = None
    PropertyManagerReadSerializer = None

class CreateFullPropertyManagerView(APIView):
    permission_classes = [IsAgent, IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if PropertyManager is None:
            return Response({'detail': 'PropertyManager model not implemented.'}, status=501)
        data = request.data
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        phone = data.get('phone')
        if not email or not password or not name:
            return Response({'detail': 'Email, password, and name are required.'}, status=400)
        # 1. Create user in Firebase
        try:
            firebase_user = firebase_auth.create_user(email=email, password=password, display_name=name)
            firebase_uid = firebase_user.uid
        except Exception as e:
            return Response({'detail': f'Firebase user creation failed: {str(e)}'}, status=400)
        # 2. Create Django user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'firebase_uid': firebase_uid,
                'name': name,
                'role': 'property_manager',
                'is_active': True,
            }
        )
        if not created:
            user.firebase_uid = firebase_uid
            user.name = name
            user.role = 'property_manager'
            user.is_active = True
            user.save()
        # 3. Create PropertyManager profile
        manager = PropertyManager.objects.create(
            user=user,
            name=name,
            phone=phone,
            email=email
        )
        return Response(PropertyManagerReadSerializer(manager).data, status=status.HTTP_201_CREATED)
