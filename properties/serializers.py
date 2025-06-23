from rest_framework import serializers
from properties.models import Property
from landlords.serializers import LandlordReadSerializer
from landlords.models import Landlord


class PropertyReadSerializer(serializers.ModelSerializer):
    landlord = LandlordReadSerializer()

    class Meta:
        model = Property
        fields = ['id', 'landlord', 'name', 'address', 'description', 'status', 'created_at']


class PropertyWriteSerializer(serializers.ModelSerializer):
    landlord = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.all()
    )

    class Meta:
        model = Property
        fields = ['id', 'landlord', 'name', 'address', 'description', 'status']
        read_only_fields = ['id']