# rental_backend/urls.py
import logging
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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

# API v1 URL patterns
api_v1_patterns = [
    # Auth 
    path('auth/', include('accounts.urls')),
    # Modules
    path('agents/', include('agents.urls')),
    path('property-managers/', include('property_manager.urls')),  # Renamed for consistency
    path('landlords/', include('landlords.urls')),
    path('properties/', include('properties.urls')),
    path('units/', include('units.urls')),
    path('tenants/', include('tenants.urls')),
    path('payments/', include('payments.urls')),
    path('communications/', include('communications.urls')),  # Renamed from sms for better clarity
    path('lease/', include('lease.urls')),
    # JWT Auth Endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
]

# Add this at the end of the file
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)