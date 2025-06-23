from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from firebase_admin import auth as firebase_auth
from accounts.models import User
from agents.models import Agent
from agents.serializers import AgentReadSerializer
from rental_backend.permissions import IsAdminOrLandlord
from rest_framework.permissions import IsAuthenticated

class CreateFullAgentView(APIView):
    permission_classes = [IsAdminOrLandlord, IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        from firebase_admin import _auth_utils
        data = request.data
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        phone = data.get('phone')
        if not email or not password or not name:
            return Response({'detail': 'Email, password, and name are required.'}, status=400)
        # 1. Try to get or create user in Firebase
        try:
            try:
                firebase_user = firebase_auth.get_user_by_email(email)
                firebase_uid = firebase_user.uid
            except _auth_utils.UserNotFoundError:
                firebase_user = firebase_auth.create_user(email=email, password=password, display_name=name)
                firebase_uid = firebase_user.uid
        except Exception as e:
            return Response({'detail': f'Firebase user creation failed: {str(e)}'}, status=400)
        # 2. Get or create Django user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'firebase_uid': firebase_uid,
                'name': name,
                'role': 'agent',
                'is_active': True,
            }
        )
        if not created:
            user.firebase_uid = firebase_uid
            user.name = name
            user.role = 'agent'
            user.is_active = True
            user.save()
        # 3. Create Agent profile if not exists
        agent, agent_created = Agent.objects.get_or_create(
            user=user
        )
        return Response(AgentReadSerializer(agent).data, status=status.HTTP_201_CREATED)
