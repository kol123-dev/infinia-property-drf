# communications/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from communications.views import SmsMessageViewSet, SmsTemplateViewSet

router = SimpleRouter()
router.register('messages', SmsMessageViewSet, basename='sms')
router.register('templates', SmsTemplateViewSet, basename='sms-templates')

urlpatterns = [
    path('', include(router.urls)),
]