from rest_framework import serializers
from tenants.models import Tenant, TenantStatus, EmergencyContact, Contract, TenantGroup
from landlords.serializers import LandlordReadSerializer
from landlords.models import Landlord  # Add this import
from units.models import Unit
from properties.serializers import SimplePropertySerializer
from django.contrib.auth import get_user_model  # Add this import

User = get_user_model()  # Add this line
from accounts.serializers import UserReadSerializer

class SimpleUnitSerializer(serializers.ModelSerializer):
    property = SimplePropertySerializer(source='property_fk', read_only=True)
    
    class Meta:
        model = Unit
        fields = ['id', 'unit_id', 'unit_number', 'type', 'status', 'floor', 'size', 'rent', 'property']

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['name', 'phone', 'relationship']

class SimpleUnitSerializer(serializers.ModelSerializer):
    property = SimplePropertySerializer(source='property_fk', read_only=True)
    
    class Meta:
        model = Unit
        fields = ['id', 'unit_id', 'unit_number', 'type', 'status', 'floor', 'size', 'rent', 'property']

# Add this import at the top with other imports
from accounts.serializers import UserReadSerializer

class TenantReadSerializer(serializers.ModelSerializer):
    current_unit = SimpleUnitSerializer(read_only=True)
    landlord = LandlordReadSerializer(read_only=True)
    emergency_contact = EmergencyContactSerializer(read_only=True)
    tenant_status = serializers.ChoiceField(choices=TenantStatus.choices, source='status')
    user = UserReadSerializer(read_only=True)  # Add this line

    class Meta:
        model = Tenant
        fields = [
            'id', 'tenant_id', 'user', 'landlord', 'current_unit',
            'phone', 'date_of_birth', 'move_in_date', 'tenant_status',
            'emergency_contact', 'created_at'
        ]

class TenantWriteSerializer(serializers.ModelSerializer):
    current_unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        required=False,
        allow_null=True
    )
    landlord = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.all(),
        required=False,
        allow_null=True
    )
    emergency_contact = EmergencyContactSerializer(required=False)
    tenant_status = serializers.ChoiceField(choices=TenantStatus.choices, source='status')
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Tenant
        fields = [
            'id', 'tenant_id', 'user', 'landlord', 'current_unit',
            'phone', 'date_of_birth', 'move_in_date', 'tenant_status',
            'emergency_contact', 'created_at'
        ]

    def create(self, validated_data):
        emergency_contact_data = validated_data.pop('emergency_contact', None)
        
        # Create the tenant instance
        tenant = Tenant.objects.create(**validated_data)
        
        # Create emergency contact if data is provided
        if emergency_contact_data:
            EmergencyContact.objects.create(tenant=tenant, **emergency_contact_data)
        
        return tenant
        read_only_fields = ['id', 'tenant_id']

    def update(self, instance, validated_data):
        emergency_contact_data = validated_data.pop('emergency_contact', None)
        user_data = validated_data.pop('user', None)
        
        # Update user information if provided
        if user_data:
            user = instance.user
            if user:
                for attr, value in user_data.items():
                    if attr not in ['email', 'role', 'is_active']:  # Protect sensitive fields
                        setattr(user, attr, value)
                user.save()
        
        # Update emergency contact if provided
        if emergency_contact_data:
            emergency_contact = instance.emergency_contact
            if emergency_contact:
                # Update existing emergency contact
                for attr, value in emergency_contact_data.items():
                    setattr(emergency_contact, attr, value)
                emergency_contact.save()
            else:
                # Create new emergency contact
                EmergencyContact.objects.create(tenant=instance, **emergency_contact_data)
        
        # Update tenant fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class ContractReadSerializer(serializers.ModelSerializer):
    tenant = TenantReadSerializer(read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id', 'tenant', 'start_date', 'end_date', 'file',
            'is_signed', 'signed_at', 'is_active', 'auto_renew',
            'created_at'
        ]

class ContractWriteSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all()
    )

    class Meta:
        model = Contract
        fields = [
            'id', 'tenant', 'start_date', 'end_date', 'file',
            'is_signed', 'signed_at', 'is_active', 'auto_renew'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data

class TenantGroupReadSerializer(serializers.ModelSerializer):
    landlord = LandlordReadSerializer(read_only=True)
    tenants = TenantReadSerializer(many=True, read_only=True)

    class Meta:
        model = TenantGroup
        fields = ['id', 'name', 'description', 'landlord', 'tenants', 'created_at', 'updated_at']

class TenantGroupWriteSerializer(serializers.ModelSerializer):
    landlord = serializers.PrimaryKeyRelatedField(queryset=Landlord.objects.all())
    tenants = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all(), many=True)

    class Meta:
        model = TenantGroup
        fields = ['id', 'name', 'description', 'landlord', 'tenants']
        read_only_fields = ['id']