# payments/views.py
from rest_framework import viewsets
from payments.models import Payment, PaymentReceipt
from payments.serializers import PaymentReadSerializer, PaymentWriteSerializer, PaymentReceiptReadSerializer, PaymentReceiptWriteSerializer
from rental_backend.permissions import IsLandlordOrTenantReadOnly


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    permission_classes = [IsLandlordOrTenantReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PaymentReadSerializer
        return PaymentWriteSerializer


class PaymentReceiptViewSet(viewsets.ModelViewSet):
    queryset = PaymentReceipt.objects.all()
    permission_classes = [IsLandlordOrTenantReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PaymentReceiptReadSerializer
        return PaymentReceiptWriteSerializer