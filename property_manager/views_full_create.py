from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from firebase_admin import auth as firebase_auth
from accounts.models import User
from property_manager.models import PropertyManager
from property_manager.serializers import PropertyManagerReadSerializer
from rental_backend.permissions import IsAdminOrLandlord
from rest_framework.permissions import IsAuthenticated

class CreateFullPropertyManagerView(APIView):
    permission_classes = [IsAdminOrLandlord, IsAuthenticated]

    @transaction.atomic
    def post(self, request):
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
