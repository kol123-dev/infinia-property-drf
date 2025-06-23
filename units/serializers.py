from rest_framework import serializers
from units.models import Unit
from properties.serializers import PropertyReadSerializer
from properties.models import Property


class UnitReadSerializer(serializers.ModelSerializer):
    property = PropertyReadSerializer()

    class Meta:
        model = Unit
        fields = [
            'id', 'property', 'unit_name', 'unit_type', 'status',
            'rent_amount', 'description', 'created_at'
        ]


class UnitWriteSerializer(serializers.ModelSerializer):
    property = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all()
    )

    class Meta:
        model = Unit
        fields = [
            'id', 'property', 'unit_name', 'unit_type', 'status',
            'rent_amount', 'description'
        ]
        read_only_fields = ['id']