from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Permission class that only allows access to admin users.
    Admin users are those with is_staff=True or is_superuser=True.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Permission class that allows read access to authenticated users
    but write access only to admin users.
    """

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return request.user and request.user.is_authenticated

        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permission class that allows users to access their own data
    or admin users to access all data.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Users can only access their own data
        if hasattr(obj, "student"):
            return obj.student == request.user
        elif hasattr(obj, "user"):
            return obj.user == request.user

        return False
