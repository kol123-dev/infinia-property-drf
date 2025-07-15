from rest_framework import serializers
from landlords.models import Landlord
from accounts.serializers import UserReadSerializer
from django.contrib.auth import get_user_model

# Force Django to reload this module
print("LANDLORD SERIALIZER LOADED - PROPERTIES FIELD ADDED")

User = get_user_model()

class LandlordReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()
    agent = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    class Meta:
        model = Landlord
        fields = [
            'id', 'landlord_id', 'user', 'agent', 'name', 'email',
            'phone', 'id_number', 'business_name',
            'company_registration_number', 'created_at', 'properties'
        ]
    
    def get_agent(self, obj):
        if obj.agent:
            try:
                # Import here to avoid potential circular import issues
                from agents.serializers import AgentReadSerializer
                return AgentReadSerializer(obj.agent).data
            except Exception as e:
                # Fallback to basic agent info if serialization fails
                return {
                    'id': obj.agent.id,
                    'name': obj.agent.user.get_full_name() if obj.agent.user else 'Unknown',
                    'email': obj.agent.user.email if obj.agent.user else None,
                    'phone': obj.agent.user.phone if obj.agent.user else None
                }
        return None
    
    def get_properties(self, obj):
        print(f"Getting properties for landlord {obj.id}")
        try:
            # Get all properties for this landlord
            properties = obj.properties.all()
            print(f"Found {properties.count()} properties for landlord {obj.id}")
            
            properties_data = []
            for prop in properties:
                property_data = {
                    'id': prop.id,
                    'property_id': prop.property_id,
                    'name': prop.name,
                    'address': prop.address,
                    'property_type': prop.property_type,
                    'total_units': prop.total_units,
                    'occupied_units': prop.occupied_units,
                    'vacant_units': prop.vacant_units,
                    'occupancy_rate': float(prop.occupancy_rate) if prop.occupancy_rate else 0,
                    'potential_monthly_revenue': float(prop.potential_monthly_revenue) if prop.potential_monthly_revenue else 0,
                    'actual_monthly_revenue': float(prop.actual_monthly_revenue) if prop.actual_monthly_revenue else 0,
                    'status': prop.status,
                    'created_at': prop.created_at
                }
                properties_data.append(property_data)
            
            print(f"Returning {len(properties_data)} properties for landlord {obj.id}")
            return properties_data
            
        except Exception as e:
            print(f"Error getting properties for landlord {obj.id}: {str(e)}")
            return []

class LandlordWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='landlord')
    )
    # Fix: Provide a dummy queryset initially, then override in __init__
    agent = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),  # Dummy queryset to avoid AssertionError
        required=False,
        allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports and set proper queryset
        try:
            from agents.models import Agent
            self.fields['agent'].queryset = Agent.objects.all()
        except ImportError:
            # Fallback if agents app is not available
            pass

    class Meta:
        model = Landlord
        fields = [
            'id', 'landlord_id', 'user', 'agent', 'name', 'email',
            'phone', 'id_number', 'business_name',
            'company_registration_number'
        ]
        read_only_fields = ['id', 'landlord_id']

    def validate_email(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Email cannot be empty string")
        return value

    def validate_phone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Phone number must start with '+'")
        return value