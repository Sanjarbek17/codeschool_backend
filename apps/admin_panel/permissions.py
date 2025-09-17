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


class IsActiveStudentOrTeacherOrAdmin(BasePermission):
    """
    Custom permission to only allow access to students with active payment status,
    teachers, or admin users.

    Students with 'suspended' or 'expelled' status are denied access to educational content.
    Students with 'warning' status can still access content (grace period).
    """

    message = "Access denied. Your account has been suspended due to payment issues. Please contact administration."

    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and staff have full access
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Teachers have full access
        if hasattr(request.user, "teacher_profile"):
            return True

        # For students, check payment status
        if hasattr(request.user, "student_profile"):
            try:
                from .models import StudentPaymentStatus

                payment_status = StudentPaymentStatus.objects.get(student=request.user)
                # Allow access for active, warning, and graduated students
                # Block access for suspended and expelled students
                if payment_status.status in ["suspended", "expelled"]:
                    self.message = f"Access denied. Your account status is '{payment_status.status}' due to payment issues. Please contact administration."
                    return False
                return payment_status.status in ["active", "warning", "graduated"]
            except StudentPaymentStatus.DoesNotExist:
                # If no payment status exists, treat as active (new student)
                return True

        # Default deny for any other user type
        return False

    def has_object_permission(self, request, view, obj):
        # Object-level permissions same as general permissions
        return self.has_permission(request, view)


class IsActiveStudentForContentAccess(BasePermission):
    """
    More strict permission specifically for content access.
    Only allows students with 'active' or 'graduated' status.
    Students with 'warning' status get limited access.
    """

    message = "Access denied. Please ensure your payment is up to date to access this content."

    def has_permission(self, request, view):
        from rest_framework.permissions import SAFE_METHODS

        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and staff have full access
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Teachers have full access
        if hasattr(request.user, "teacher_profile"):
            return True

        # For students, check payment status
        if hasattr(request.user, "student_profile"):
            try:
                from .models import StudentPaymentStatus

                payment_status = StudentPaymentStatus.objects.get(student=request.user)

                # Custom messages based on status
                if payment_status.status == "warning":
                    self.message = "Limited access: You have overdue payments. Please make a payment to maintain full access."
                elif payment_status.status in ["suspended", "expelled"]:
                    self.message = f"Access denied. Your account is '{payment_status.status}' due to payment issues. Please contact administration."

                # Read-only access for warning status students (can view but not interact)
                if (
                    payment_status.status == "warning"
                    and request.method in SAFE_METHODS
                ):
                    return True

                # Full access for active and graduated students
                return payment_status.status in ["active", "graduated"]

            except StudentPaymentStatus.DoesNotExist:
                # If no payment status exists, treat as active (new student)
                return True

        # Default deny
        return False


class CanAccessHomework(BasePermission):
    """
    Permission for homework and assignment access.
    More restrictive - only active students can access homework.
    """

    message = "Access denied. Only students with active payment status can access homework and assignments."

    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins and staff have full access
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Teachers have full access
        if hasattr(request.user, "teacher_profile"):
            return True

        # For students, check payment status
        if hasattr(request.user, "student_profile"):
            try:
                from .models import StudentPaymentStatus

                payment_status = StudentPaymentStatus.objects.get(student=request.user)

                # Custom message for different statuses
                if payment_status.status == "warning":
                    self.message = "Limited access: Please make your overdue payment to access homework and assignments."
                elif payment_status.status in ["suspended", "expelled"]:
                    self.message = f"Access denied. Your account is '{payment_status.status}'. Please contact administration to restore access."

                # Only active and graduated students can access homework
                return payment_status.status in ["active", "graduated"]

            except StudentPaymentStatus.DoesNotExist:
                # If no payment status exists, treat as active (new student)
                return True

        # Default deny
        return False


def get_student_payment_status(user):
    """
    Utility function to get student payment status.
    Returns the status string or 'active' if no status exists.
    """
    if not hasattr(user, "student_profile"):
        return "active"  # Not a student

    try:
        from .models import StudentPaymentStatus

        payment_status = StudentPaymentStatus.objects.get(student=user)
        return payment_status.status
    except StudentPaymentStatus.DoesNotExist:
        return "active"  # Default to active for new students


def is_student_suspended(user):
    """
    Utility function to check if a student is suspended or expelled.
    """
    status = get_student_payment_status(user)
    return status in ["suspended", "expelled"]


def can_student_access_content(user):
    """
    Utility function to check if student can access educational content.
    """
    if not hasattr(user, "student_profile"):
        return True  # Not a student (teacher/admin)

    status = get_student_payment_status(user)
    return status in ["active", "warning", "graduated"]


def can_student_submit_assignments(user):
    """
    Utility function to check if student can submit assignments.
    """
    if not hasattr(user, "student_profile"):
        return True  # Not a student (teacher/admin)

    status = get_student_payment_status(user)
    return status in ["active", "graduated"]
