from rest_framework import serializers
from accounts.models import User


class UserReadSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'role', 'is_active']


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'role', 'password']
        extra_kwargs = {
            'id': {'read_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'phone',
            'role',
            'is_active',
            'bio',
            'profile_image',
            'country',
            'city_state',
            'gender',
            'date_of_birth'
        ]
        read_only_fields = ['email', 'role', 'is_active', 'full_name']