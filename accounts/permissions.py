from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superuser can access everything
        if user.is_superuser:
            return True
            
        # Check user role
        if user.role == 'admin':
            return True
        elif user.role == 'agent':
            # Agents can access properties they manage
            if hasattr(obj, 'agent'):
                return obj.agent.user == user
            # For units under properties they manage
            if hasattr(obj, 'property_fk'):
                return obj.property_fk.agent.user == user
            # For tenants under properties they manage
            if hasattr(obj, 'landlord'):
                managed_properties = obj.landlord.properties.filter(agent__user=user)
                return managed_properties.exists()
            return False
        elif user.role == 'current_unit':
            return obj.current_unit.property.agent.user == user
        elif user.role == 'landlord':
            # Landlords can access their own properties
            if hasattr(obj, 'landlord'):
                return obj.landlord.user == user
            # For tenants in their properties
            elif hasattr(obj, 'current_unit'):
                return obj.current_unit.property.landlord.user == user
        elif user.role == 'tenant':
            # Tenants can only access their own data
            if hasattr(obj, 'user'):
                return obj.user == user
            
        return False


# Add these classes to accounts/permissions.py

class IsAdmin(permissions.BasePermission):
    """Only admins can access/modify."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsAgent(permissions.BasePermission):
    """Only agents can access/modify."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'agent')

class IsLandlord(permissions.BasePermission):
    """Only landlords can access/modify."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'landlord')

class IsTenant(permissions.BasePermission):
    """Only tenants can access/modify."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'tenant')

class IsAdminOrLandlord(permissions.BasePermission):
    """Allow access to admins and landlords."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   (request.user.role in ['admin', 'landlord'] or request.user.is_staff or request.user.is_superuser))

class IsLandlordOrTenantReadOnly(permissions.BasePermission):
    """Allow landlords full access, tenants read-only access."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'landlord'] or request.user.is_staff or request.user.is_superuser:
            return True
        if request.user.role == 'tenant':
            return request.method in permissions.SAFE_METHODS
        return False