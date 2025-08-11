from rest_framework import permissions


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow teachers and admins to modify resources.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a teacher or admin."""
        if not request.user.is_authenticated:
            return False
        
        # Allow admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow teachers
        return hasattr(request.user, 'teacher_profile')

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        # Allow admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow teachers (specific logic can be overridden in views)
        return hasattr(request.user, 'teacher_profile')


class IsStudentOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow students and admins.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a student or admin."""
        if not request.user.is_authenticated:
            return False
        
        # Allow admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow students
        return hasattr(request.user, 'student_profile')


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object
        return obj.user == request.user


class IsTeacherOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow teachers to modify, others to read only.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        if not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for teachers and admins
        return (
            request.user.is_staff or 
            request.user.is_superuser or 
            hasattr(request.user, 'teacher_profile')
        )


class IsAssignedTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission for teachers assigned to specific lessons/content.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a teacher or admin."""
        if not request.user.is_authenticated:
            return False
        
        # Allow admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow teachers
        return hasattr(request.user, 'teacher_profile')

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions for assigned teachers."""
        # Allow admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow teachers who are assigned to the lesson/content
        if hasattr(request.user, 'teacher_profile'):
            # Check if object has teachers attribute (like Lessons)
            if hasattr(obj, 'teachers'):
                return obj.teachers.filter(id=request.user.teacher_profile.id).exists()
            # Check if object has lesson attribute (like Homework)
            elif hasattr(obj, 'lesson') and hasattr(obj.lesson, 'teachers'):
                return obj.lesson.teachers.filter(id=request.user.teacher_profile.id).exists()
            # Check if object has homework attribute (like Task)
            elif hasattr(obj, 'homework') and hasattr(obj.homework.lesson, 'teachers'):
                return obj.homework.lesson.teachers.filter(id=request.user.teacher_profile.id).exists()
        
        return False


class IsStudentOwnerOrTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission for student submissions and progress.
    Students can only access their own data, teachers can access assigned students' data.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        # Allow admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow students to access their own data
        if hasattr(request.user, 'student_profile') and hasattr(obj, 'student'):
            return obj.student.id == request.user.student_profile.id
        
        # Allow teachers assigned to the related lesson
        if hasattr(request.user, 'teacher_profile'):
            # For progress and submissions, check if teacher is assigned to the lesson
            if hasattr(obj, 'homework') and hasattr(obj.homework.lesson, 'teachers'):
                return obj.homework.lesson.teachers.filter(id=request.user.teacher_profile.id).exists()
            elif hasattr(obj, 'task') and hasattr(obj.task.homework.lesson, 'teachers'):
                return obj.task.homework.lesson.teachers.filter(id=request.user.teacher_profile.id).exists()
        
        return False
