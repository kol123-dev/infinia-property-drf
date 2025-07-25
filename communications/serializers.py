from rest_framework import serializers
from communications.models import SmsMessage, SmsTemplate  # Add SmsTemplate import
from tenants.serializers import TenantReadSerializer
from landlords.serializers import LandlordReadSerializer
from tenants.models import Tenant
from landlords.models import Landlord



class SmsMessageReadSerializer(serializers.ModelSerializer):
    recipients = TenantReadSerializer(many=True)
    landlord = LandlordReadSerializer()

    class Meta:
        model = SmsMessage
        fields = [
            'id', 'landlord', 'recipients', 'body', 'status',
            'external_message_id', 'error_message', 'sent_at', 'updated_at'
        ]


class SmsMessageWriteSerializer(serializers.ModelSerializer):
    recipients = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        many=True
    )
    landlord = serializers.PrimaryKeyRelatedField(
        queryset=Landlord.objects.all()
    )

    class Meta:
        model = SmsMessage
        fields = [
            'id', 'landlord', 'recipients', 'body', 'status',
            'external_message_id', 'error_message'
        ]
        read_only_fields = ['id', 'status', 'sent_at', 'updated_at']


class SmsTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsTemplate
        fields = ['id', 'name', 'content', 'landlord', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']