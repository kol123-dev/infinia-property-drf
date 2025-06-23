from rest_framework import serializers
from property_manager.models import PropertyManager
from accounts.serializers import UserReadSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class PropertyManagerReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    class Meta:
        model = PropertyManager
        fields = ['id', 'user', 'created_at']

class PropertyManagerWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='property_manager'))
    class Meta:
        model = PropertyManager
        fields = ['id', 'user']
        read_only_fields = ['id']
