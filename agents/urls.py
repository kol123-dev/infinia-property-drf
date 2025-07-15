from django.urls import path, include
from rest_framework.routers import SimpleRouter
from agents.views import AgentViewSet

router = SimpleRouter()
router.register('', AgentViewSet, basename='agent')

urlpatterns = [
    path('', include(router.urls)),
]
