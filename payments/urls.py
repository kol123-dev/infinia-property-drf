# payments/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from payments.views import PaymentViewSet, PaymentReceiptViewSet

router = SimpleRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'receipts', PaymentReceiptViewSet)

urlpatterns = [
    path('', include(router.urls)),
]