from rest_framework import serializers
from accounts.models import User


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'phone', 'role', 'is_active']


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'phone', 'role', 'password']
        extra_kwargs = {
            'id': {'read_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)