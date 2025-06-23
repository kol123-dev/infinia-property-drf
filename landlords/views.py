# landlords/views.py
from rest_framework import viewsets
from landlords.models import Landlord
from landlords.serializers import LandlordReadSerializer, LandlordWriteSerializer
from rental_backend.permissions import IsAdminOrLandlord, IsLandlordOrTenantReadOnly


class LandlordViewSet(viewsets.ModelViewSet):
    queryset = Landlord.objects.all()
    permission_classes = [IsAdminOrLandlord]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LandlordReadSerializer
        return LandlordWriteSerializer

    def create(self, request, *args, **kwargs):
        # Only agents can create landlords
        user = request.user
        if not user or not user.is_authenticated or getattr(user, 'role', None) != 'agent':
            from rest_framework.permissions import IsAuthenticated
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only agents can create landlords.')
        # Always assign the created landlord to the current agent
        data = request.data.copy()
        data['agent'] = user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)