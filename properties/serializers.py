from rest_framework import serializers
from django.db.models import Avg, F, Sum
from django.utils import timezone
from properties.models import Property, PropertyType, ResidentialType, BuildingType, UnitType, RevenueHistory
from landlords.models import Landlord
from units.models import UnitStatus  # Add this import
import logging

logger = logging.getLogger(__name__)

# Force Django to reload this module
print("SERIALIZER LOADED - NEW VERSION - LANDLORD FIX")

class UnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ['name', 'count']

class RevenueHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueHistory
        fields = ['month', 'amount']

# Simple landlord serializer to avoid circular imports
class SimpleLandlordSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Landlord
        fields = ['id', 'landlord_id', 'business_name', 'user']
    
    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
                'full_name': obj.user.full_name,
            }
        return None

class PropertyReadSerializer(serializers.ModelSerializer):
    # Use direct serializer instead of SerializerMethodField
    landlord = SimpleLandlordSerializer(read_only=True)
    agent = serializers.SerializerMethodField()
    property_type = serializers.ChoiceField(choices=PropertyType.choices)
    residential_type = serializers.ChoiceField(choices=ResidentialType.choices, required=False)
    building_type = serializers.ChoiceField(choices=BuildingType.choices)
    location = serializers.SerializerMethodField()
    units = serializers.SerializerMethodField()
    financials = serializers.SerializerMethodField()
    unit_types = UnitTypeSerializer(many=True, read_only=True)
    revenue_history = RevenueHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'property_id', 'name', 'landlord', 'agent', 'property_type',
            'residential_type', 'building_type', 'location', 'units',
            'financials', 'occupancy_rate', 'created_at', 'description',
            'unit_types', 'revenue_history'
        ]

    def get_location(self, obj):
        return {
            'address': obj.address,
            'coordinates': {
                'lat': float(obj.latitude) if obj.latitude else None,
                'lng': float(obj.longitude) if obj.longitude else None
            }
        }

    def get_units(self, obj):
        return {
            'summary': {
                'total': obj.total_units,
                'occupied': obj.occupied_units,
                'vacant': obj.vacant_units,
                'underMaintenance': obj.under_maintenance_units,
                'occupancyRate': float(obj.occupancy_rate)
            },
            'distribution': {
                unit_type.name: {
                    'total': unit_type.count,
                    'occupied': obj.units.filter(type=unit_type.name, status=UnitStatus.OCCUPIED).count(),
                    'averageRent': float(obj.units.filter(type=unit_type.name).aggregate(avg=Avg('rent'))['avg'] or 0)
                } for unit_type in obj.unit_types.all()
            },
            'metrics': {
                'averageRent': float(obj.units.aggregate(avg=Avg('rent'))['avg'] or 0),
                'averageOccupancyDuration': obj.units.filter(status=UnitStatus.OCCUPIED)
                    .aggregate(avg=Avg(F('lease_end_date') - F('lease_start_date')))['avg'],
                'expiringLeases': obj.units.filter(
                    status=UnitStatus.OCCUPIED,
                    lease_end_date__lte=timezone.now() + timezone.timedelta(days=30)
                ).count()
            }
        }

    def get_financials(self, obj):
        return {
            'summary': {
                'potentialMonthlyRevenue': float(obj.potential_monthly_revenue),
                'actualMonthlyRevenue': float(obj.actual_monthly_revenue),
                'occupancyRate': float(obj.occupancy_rate),
                'revenueEfficiency': float(obj.actual_monthly_revenue / obj.potential_monthly_revenue * 100) if obj.potential_monthly_revenue else 0
            },
            'revenueHistory': RevenueHistorySerializer(obj.revenue_history.all()[:12], many=True).data,
            'unitTypeRevenue': {
                unit_type.name: float(obj.units.filter(type=unit_type.name, status=UnitStatus.OCCUPIED).aggregate(sum=Sum('rent'))['sum'] or 0)
                for unit_type in obj.unit_types.all()
            }
        }

    def get_agent(self, obj):
        if obj.agent:
            return {
                'id': obj.agent.id,
                'name': obj.agent.user.full_name if obj.agent.user else 'Unknown',
                'email': obj.agent.user.email if obj.agent.user else None,
                'phone': obj.agent.user.phone if obj.agent.user else None
            }
        return None

class PropertyWriteSerializer(serializers.ModelSerializer):
    landlord = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.all(),
        required=False,
        allow_null=True
    )
    # Add agent field for assignment - use dummy queryset initially
    agent = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.none(),  # Dummy queryset to avoid AssertionError
        required=False,
        allow_null=True
    )
    property_type = serializers.ChoiceField(choices=PropertyType.choices)
    residential_type = serializers.ChoiceField(choices=ResidentialType.choices, required=False)
    building_type = serializers.ChoiceField(choices=BuildingType.choices)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)

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
        model = Property
        fields = [
            'id', 'property_id', 'name', 'landlord', 'agent', 'property_type',
            'residential_type', 'building_type', 'address', 'latitude', 'longitude',
            'total_units', 'occupied_units', 'vacant_units', 'under_maintenance_units',
            'potential_monthly_revenue', 'actual_monthly_revenue', 'description'
        ]
        read_only_fields = ['id', 'property_id', 'occupancy_rate']

    def validate_name(self, value):
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Property name must be at least 3 characters long")
        return value  # Add this line to return the validated value

# Add this near the top of the file, after the imports
class SimplePropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'property_id', 'name', 'address']