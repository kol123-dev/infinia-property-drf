# rental_backend/urls.py
import logging
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

logger = logging.getLogger(__name__)

# Log all incoming requests
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        logger.info("\n=== Incoming Request ===")
        logger.info(f"Path: {request.path}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Headers: {dict(request.headers) if hasattr(request, 'headers') else 'No headers'}")
        
        # Process the request
        response = self.get_response(request)
        return response

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('api/auth/', include('accounts.urls')),

    # Modules
    path('api/agents/', include('agents.urls')),
    path('api/property_manager/', include('property_manager.urls')),
    path('api/landlords/', include('landlords.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/units/', include('units.urls')),
    path('api/tenants/', include('tenants.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/sms/', include('communications.urls')),

    # JWT Auth Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]