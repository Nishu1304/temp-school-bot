from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrTeacher(BasePermission):
    """
    Custom permission:
    - Admins: Full access (GET, POST, PUT, DELETE)
    - Teachers: Read-only access (GET)
    - Others: No access
    """

    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS for teachers
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated and (
                request.user.is_staff or getattr(request.user, "is_teacher", False)
            )

        # Allow full access for Admins only
        return request.user.is_authenticated and request.user.is_staff
