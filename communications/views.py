from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from communications.models import SmsMessage, SmsTemplate
from communications.serializers import SmsMessageReadSerializer, SmsMessageWriteSerializer, SmsTemplateSerializer
from communications.services import SMSService
from rest_framework.exceptions import ValidationError

class SmsMessageViewSet(viewsets.ModelViewSet):
    queryset = SmsMessage.objects.all()
    permission_classes = [AllowAny]
    sms_service = SMSService()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return SmsMessageReadSerializer
        return SmsMessageWriteSerializer

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        body = request.data.get('body')
        recipient_groups = request.data.get('recipient_groups', [])
        individual_recipients = request.data.get('individual_recipients', [])
        
        if not body:
            return Response(
                {'error': 'Message body is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not recipient_groups and not individual_recipients:
            return Response(
                {'error': 'At least one recipient or group is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the landlord based on user role
            user = request.user
            landlord = None

            if user.role == 'landlord' and hasattr(user, 'landlord_profile'):
                landlord = user.landlord_profile
            elif user.role == 'agent' and hasattr(user, 'agent_profile'):
                # Get the first landlord managed by this agent
                landlord = user.agent_profile.managed_landlords.first()

            if not landlord:
                return Response(
                    {'error': 'User does not have permission to send messages'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Send the message using AfricasTalking
            result = self.sms_service.send_sms(
                recipients=individual_recipients,
                message=body
            )
            
            # Create message record
            sms_message = SmsMessage.objects.create(
                body=body,
                status='sent',
                external_message_id=result.get('message_id'),
                landlord=landlord  # Set the landlord
            )
            
            serializer = SmsMessageReadSerializer(sms_message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        # Get the landlord based on user role
        user = request.user
        landlord = None

        if user.role == 'landlord' and hasattr(user, 'landlord_profile'):
            landlord = user.landlord_profile
        elif user.role == 'agent' and hasattr(user, 'agent_profile'):
            # Get the first landlord managed by this agent
            landlord = user.agent_profile.managed_landlords.first()

        if not landlord:
            return Response(
                {'error': 'User does not have permission to send messages'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Add landlord to the request data
        request.data['landlord'] = landlord.id
        
        # Convert recipients array to the expected format
        if 'recipients' in request.data and isinstance(request.data['recipients'], list):
            request.data['recipients'] = request.data['recipients']

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the message first
        sms_message = serializer.save(status='queued')
        
        try:
            # Send the message using AfricasTalking
            result = self.sms_service.send_sms(
                recipients=sms_message.recipients.all(),
                message=sms_message.body
            )
            
            # Update the message with the response
            sms_message.status = 'sent'
            sms_message.external_message_id = result.get('message_id')
            sms_message.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            sms_message.status = 'failed'
            sms_message.error_message = str(e)
            sms_message.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SmsTemplateViewSet(viewsets.ModelViewSet):
    queryset = SmsTemplate.objects.all()
    serializer_class = SmsTemplateSerializer
    permission_classes = [AllowAny]  # You should replace this with appropriate permissions

    def get_queryset(self):
        user = self.request.user
        if user.role == 'landlord' and hasattr(user, 'landlord_profile'):
            return SmsTemplate.objects.filter(landlord=user.landlord_profile)
        elif user.role == 'agent' and hasattr(user, 'agent_profile'):
            # Get templates for all landlords managed by this agent
            return SmsTemplate.objects.filter(landlord__agent=user.agent_profile)
        return SmsTemplate.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'landlord' and hasattr(user, 'landlord_profile'):
            serializer.save(landlord=user.landlord_profile)
        elif user.role == 'agent' and hasattr(user, 'agent_profile'):
            # If agent is creating a template, assign it to the landlord they manage
            # Note: This assumes an agent manages one landlord. If they manage multiple,
            # you'll need to require the landlord_id in the request data
            landlord = user.agent_profile.managed_landlords.first()
            if landlord:
                serializer.save(landlord=landlord)
            else:
                raise ValidationError("Agent is not associated with any landlord")
        else:
            raise ValidationError("User does not have permission to create templates")

    def perform_update(self, serializer):
        user = self.request.user
        template = self.get_object()
        
        if user.role == 'landlord' and hasattr(user, 'landlord_profile'):
            if template.landlord != user.landlord_profile:
                raise ValidationError("You can only update your own templates")
        elif user.role == 'agent' and hasattr(user, 'agent_profile'):
            if template.landlord.agent != user.agent_profile:
                raise ValidationError("You can only update templates for landlords you manage")
        else:
            raise ValidationError("User does not have permission to update templates")
            
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        
        if user.role == 'landlord' and hasattr(user, 'landlord_profile'):
            if instance.landlord != user.landlord_profile:
                raise ValidationError("You can only delete your own templates")
        elif user.role == 'agent' and hasattr(user, 'agent_profile'):
            if instance.landlord.agent != user.agent_profile:
                raise ValidationError("You can only delete templates for landlords you manage")
        else:
            raise ValidationError("User does not have permission to delete templates")
            
        instance.delete()