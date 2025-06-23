from django.urls import path, include
from rest_framework.routers import SimpleRouter
from agents.views import AgentViewSet
from agents.views_full_create import CreateFullAgentView

router = SimpleRouter()
router.register(r'', AgentViewSet, basename='agent')

urlpatterns = [
    path('create_full/', CreateFullAgentView.as_view(), name='create_full_agent'),
    path('', include(router.urls)),
]
