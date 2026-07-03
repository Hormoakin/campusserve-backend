from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role is not None
                and request.user.role.name == "admin")

class IsMaintenanceOfficer(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role is not None
                and request.user.role.name == "maintenance_officer")

class IsAdminOrOfficer(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role is not None
                and request.user.role.name in ["admin", "maintenance_officer"])

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.role and request.user.role.name == "admin":
            return True
        if hasattr(obj, "requester"):
            return obj.requester == request.user
        return obj == request.user
