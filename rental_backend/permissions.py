# rental_backend/permissions.py
from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsAdmin(permissions.BasePermission):
    """Only admins can access/modify."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin')

class IsAgent(permissions.BasePermission):
    """Only agents can access/modify."""
    def has_permission(self, request, view):
        print("\n=== DEBUG: IsAgent Permission Check ===")
        print(f"Request user: {request.user}")
        print(f"Authenticated: {getattr(request.user, 'is_authenticated', False)}")
        print(f"User email: {getattr(request.user, 'email', 'no-email')}")
        print(f"User role: {getattr(request.user, 'role', 'no-role')}")
        print(f"User is active: {getattr(request.user, 'is_active', 'no-is_active')}")
        
        if not getattr(request.user, 'is_authenticated', False):
            print("Permission Denied: User not authenticated")
            return False

        user_role = getattr(request.user, 'role', '').lower()
        is_agent = user_role == 'agent'
        
        if not is_agent:
            print(f"Permission Denied: User role is '{user_role}', expected 'agent'")
        else:
            print("Permission Granted: User is an agent")
            
        return is_agent
        
class IsLandlord(permissions.BasePermission):
    """
    Only landlords can access or modify resources.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            print("Permission Denied: User not authenticated")
            return False
            
        print(f"User role: {getattr(request.user, 'role', 'No role attribute')}")
        print(f"User is authenticated: {request.user.is_authenticated}")
        print(f"User attributes: {dir(request.user)}")
        
        has_permission = request.user.role == 'landlord'
        if not has_permission:
            print(f"Permission Denied: User role is {getattr(request.user, 'role', 'not set')}, expected 'landlord'")
            
        return has_permission


class IsTenant(permissions.BasePermission):
    """
    Only tenants can access certain read-only endpoints.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'tenant')


class IsLandlord(BasePermission):
    """
    Only landlords can access these endpoints.
    """
    def has_permission(self, request, view):
        import logging
        logger = logging.getLogger(__name__)
        
        if not request.user or not request.user.is_authenticated:
            logger.warning(f"Permission denied: User not authenticated")
            return False
            
        logger.info(f"Checking landlord permission for user: {request.user.email}, Role: {getattr(request.user, 'role', 'no role')}")
        
        is_landlord = bool(request.user.role == 'landlord')
        if not is_landlord:
            logger.warning(f"Permission denied: User {request.user.email} is not a landlord")
            
        return is_landlord


class IsAdminOrLandlord(BasePermission):
    """
    Allows full access to admins and landlords (including Django admin users).
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if IsAdmin().has_permission(request, view) or user.role == 'landlord' or user.is_staff or user.is_superuser:
            return True
        return False

class IsLandlordOrTenantReadOnly(permissions.BasePermission):
    """
    Allow landlords full access, tenants only safe methods (GET).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Allow admin and landlord roles, and Django admin users
        if getattr(request.user, 'role', None) in ('admin', 'landlord') or \
           getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
            return True
        if getattr(request.user, 'role', None) == 'tenant':
            return request.method in permissions.SAFE_METHODS
        return False