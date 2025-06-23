from django.urls import path, include
from rest_framework.routers import SimpleRouter
from accounts.views import FirebaseLoginView, CreateUserView, DebugAuthView, ListUsersView

# No UserViewSet needed if you're not exposing user CRUD
# Remove that import + router registration

urlpatterns = [
    path('firebase-login/', FirebaseLoginView.as_view(), name='firebase_login'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('debug-auth/', DebugAuthView.as_view(), name='debug_auth'),  # Add this line
    path('users/', ListUsersView.as_view(), name='list_users'),
]