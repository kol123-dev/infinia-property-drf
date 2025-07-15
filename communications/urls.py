# communications/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from communications.views import SmsMessageViewSet

router = SimpleRouter()
router.register('', SmsMessageViewSet, basename='sms')  # Remove r'sms' prefix

urlpatterns = [
    path('', include(router.urls)),
]