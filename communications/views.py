# communications/views.py
from rest_framework import viewsets
from communications.models import SmsMessage
from communications.serializers import SmsMessageReadSerializer, SmsMessageWriteSerializer
from rental_backend.permissions import IsLandlord


class SmsMessageViewSet(viewsets.ModelViewSet):
    queryset = SmsMessage.objects.all()
    permission_classes = [IsLandlord]  # Only landlords can send SMS

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return SmsMessageReadSerializer
        return SmsMessageWriteSerializer