from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from landlords.models import Landlord
from landlords.serializers import LandlordReadSerializer, LandlordWriteSerializer

class LandlordViewSet(viewsets.ModelViewSet):
    queryset = Landlord.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LandlordReadSerializer
        return LandlordWriteSerializer