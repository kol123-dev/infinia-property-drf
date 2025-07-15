from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from communications.models import SmsMessage
from communications.serializers import SmsMessageReadSerializer, SmsMessageWriteSerializer
from communications.services import SMSService

class SmsMessageViewSet(viewsets.ModelViewSet):
    queryset = SmsMessage.objects.all()
    permission_classes = [AllowAny]
    sms_service = SMSService()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return SmsMessageReadSerializer
        return SmsMessageWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the message first
        sms_message = serializer.save(status='queued')
        
        try:
            # Send the message using AfricasTalking
            result = self.sms_service.send_sms(
                recipients=sms_message.recipients,
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