from rest_framework import serializers
from .models import Homework, Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    Includes test case and submission counts.
    """
    test_case_count = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'homework', 'title', 'description',
            'test_case_count', 'submission_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'test_case_count', 'submission_count']

    def get_test_case_count(self, obj):
        """Get the number of test cases for this task."""
        return obj.get_test_case_count()
    
    def get_submission_count(self, obj):
        """Get the number of submissions for this task."""
        return obj.get_submission_count()


class TaskListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for task list views.
    """
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    lesson_title = serializers.CharField(source='homework.lesson.title', read_only=True)
    test_case_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'homework_title', 'lesson_title',
            'test_case_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'homework_title', 'lesson_title']

    def get_test_case_count(self, obj):
        """Get the number of test cases for this task."""
        return obj.get_test_case_count()


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating tasks.
    """
    
    class Meta:
        model = Task
        fields = ['homework', 'title', 'description']

    def validate_title(self, value):
        """Validate task title is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_description(self, value):
        """Validate task description is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Serializer for Homework model.
    Includes task information and completion rate.
    """
    task_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_teachers = serializers.SerializerMethodField()
    tasks = TaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = Homework
        fields = [
            'id', 'lesson', 'lesson_title', 'lesson_teachers', 'title', 'description',
            'task_count', 'completion_rate', 'tasks',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'task_count', 'completion_rate', 'lesson_title']

    def get_task_count(self, obj):
        """Get the number of tasks in this homework."""
        return obj.get_task_count()
    
    def get_completion_rate(self, obj):
        """Get the completion rate for this homework."""
        return obj.get_completion_rate()
    
    def get_lesson_teachers(self, obj):
        """Get teacher names for the lesson."""
        return [
            {
                'id': teacher.id,
                'full_name': teacher.full_name,
                'username': teacher.user.username
            }
            for teacher in obj.lesson.teachers.all()
        ]


class HomeworkListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for homework list views.
    """
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    task_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'title', 'description', 'lesson_title',
            'task_count', 'completion_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'lesson_title']

    def get_task_count(self, obj):
        """Get the number of tasks in this homework."""
        return obj.get_task_count()
    
    def get_completion_rate(self, obj):
        """Get the completion rate for this homework."""
        return round(obj.get_completion_rate(), 1)


class HomeworkCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating homework.
    """
    
    class Meta:
        model = Homework
        fields = ['lesson', 'title', 'description']

    def validate_title(self, value):
        """Validate homework title is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_description(self, value):
        """Validate homework description is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()

    def validate_lesson(self, value):
        """Validate that the lesson exists and user has permission."""
        if not value:
            raise serializers.ValidationError("Lesson is required.")
        
        # Check if the current user is a teacher assigned to this lesson
        request = self.context.get('request')
        if request and hasattr(request.user, 'teacher_profile'):
            if not value.teachers.filter(id=request.user.teacher_profile.id).exists():
                raise serializers.ValidationError(
                    "You can only create homework for lessons you are assigned to."
                )
        
        return value


class HomeworkDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for homework detail views.
    Includes full task information and statistics.
    """
    task_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_teachers = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    student_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'lesson', 'lesson_title', 'lesson_teachers', 'title', 'description',
            'task_count', 'completion_rate', 'tasks', 'student_progress',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_task_count(self, obj):
        """Get the number of tasks in this homework."""
        return obj.get_task_count()
    
    def get_completion_rate(self, obj):
        """Get the completion rate for this homework."""
        return round(obj.get_completion_rate(), 1)
    
    def get_lesson_teachers(self, obj):
        """Get teacher information for the lesson."""
        return [
            {
                'id': teacher.id,
                'full_name': teacher.full_name,
                'username': teacher.user.username,
                'phone_number': teacher.phone_number
            }
            for teacher in obj.lesson.teachers.all()
        ]
    
    def get_tasks(self, obj):
        """Get detailed task information."""
        tasks = obj.tasks.all()
        return [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'test_case_count': task.get_test_case_count(),
                'submission_count': task.get_submission_count(),
                'created_at': task.created_at,
                'updated_at': task.updated_at
            }
            for task in tasks
        ]
    
    def get_student_progress(self, obj):
        """Get student progress statistics for this homework."""
        from apps.progress.models import HomeworkProgress
        
        progress_records = HomeworkProgress.objects.filter(homework=obj)
        total_students = progress_records.count()
        completed_students = progress_records.filter(is_completed=True).count()
        
        return {
            'total_students': total_students,
            'completed_students': completed_students,
            'completion_percentage': round((completed_students / total_students * 100), 1) if total_students > 0 else 0
        }
