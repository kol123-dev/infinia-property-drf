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
    landlord_profile = serializers.SerializerMethodField()
    agent_profile = serializers.SerializerMethodField()

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
            'landlord_profile',
            'agent_profile',
            'country',
            'city_state',
            'gender',
            'date_of_birth'
        ]
        read_only_fields = ['email', 'role', 'is_active', 'full_name']

    def get_landlord_profile(self, obj):
        if obj.role == 'landlord' and hasattr(obj, 'landlord_profile'):
            return {'id': obj.landlord_profile.id}
        return None

    def get_agent_profile(self, obj):
        if obj.role == 'agent' and hasattr(obj, 'agent_profile'):
            return {
                'id': obj.agent_profile.id,
                'managed_landlords': [
                    {'id': landlord.id}
                    for landlord in obj.agent_profile.managed_landlords.all()
                ]
            }
        return None