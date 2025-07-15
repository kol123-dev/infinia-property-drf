from django.urls import path, include
from rest_framework.routers import SimpleRouter
from accounts.views import (
    FirebaseLoginView,
    CreateUserView,
    DebugAuthView,
    ListUsersView,
    UserProfileView  # Add this import
)

urlpatterns = [
    path('firebase-login/', FirebaseLoginView.as_view(), name='firebase-login'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('debug-auth/', DebugAuthView.as_view(), name='debug_auth'),
    path('users/', ListUsersView.as_view(), name='list_users'),
    path('me/', UserProfileView.as_view(), name='user_profile'),  # Add this path
]