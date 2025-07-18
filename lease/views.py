from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import RoleBasedPermission
from lease.models import Lease
from lease.serializers import LeaseReadSerializer, LeaseWriteSerializer

class LeaseViewSet(viewsets.ModelViewSet):
    queryset = Lease.objects.all()
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LeaseReadSerializer
        return LeaseWriteSerializer
