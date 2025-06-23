from django.contrib.auth import get_user_model  # <-- Add this import

from rest_framework import serializers
from landlords.models import Landlord
from accounts.serializers import UserReadSerializer

User = get_user_model()  # Safely references the active User model


class LandlordReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    agent = UserReadSerializer()

    class Meta:
        model = Landlord
        fields = [
            'id', 'user', 'agent', 'business_name', 'address',
            'company_registration_number', 'created_at'
        ]


class LandlordWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='landlord')
    )
    agent = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='agent'),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Landlord
        fields = [
            'id', 'user', 'agent', 'business_name', 'address',
            'company_registration_number'
        ]
        read_only_fields = ['id']